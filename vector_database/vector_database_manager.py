import time

import chromadb
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from config import settings
from ollama_helpers import get_available_ollama_host
from vector_database.srt_splitter import get_splits_from_srt


def get_chromadb_client(database_path):
	client = chromadb.PersistentClient(path=database_path)
	return client

def get_or_create_vector_database(database_path):
	host = get_available_ollama_host()
	embeddings = OllamaEmbeddings(
		model=settings.embedding_model, base_url=host
	)

	# Create vector database with Chroma
	vector_store = Chroma(
		collection_name=settings.collection_name,
		embedding_function=embeddings,
		persist_directory=database_path
	)
	return vector_store

def process_in_batches(splits, batch_size):
	num_batches = (len(splits) + batch_size - 1) // batch_size
	for i in range(0, len(splits), batch_size):
		print(f"Batch {i // batch_size + 1} of {num_batches}")
		yield splits[i:i + batch_size]

# Creates the database and populates it with the documents provided
def add_documents_to_vector_database(database_path, files_list):
	vector_store = get_or_create_vector_database(database_path)
	for filename in files_list:
		print(f"Extracting content from file: {filename}")
		splits = get_splits_from_srt(filename)
		start_time = time.time()
		if settings.show_logs:
			print(f"Obtained {len(splits)} splits of text.")
		for batch in process_in_batches(splits, settings.batch_size):
			if settings.show_logs:
				current_time = time.time()
				time_processing = current_time - start_time
				print(f"Adding batch: {batch}")
				# Shows how long its been since the processing started.
				now = time.localtime()
				print(f"{now.tm_hour}:{now.tm_min} - Time since start: {time_processing:.2f} seconds")
			_ = vector_store.add_documents(documents=batch)
		end_time = time.time()
		total_time = end_time - start_time
		print(f"Total time processing: {total_time:.2f} seconds")
	return vector_store

# Returns a list of the collections in the database
def get_collections_from_database(database_path):
	client = get_chromadb_client(database_path)
	return client.list_collections()

# Delete the collections in the database
def delete_existing_collections(database_path):
	client = get_chromadb_client(database_path)
	for collection in client.list_collections():
		collection_name = collection.name
		print(f"Deleting collection {collection_name}")
		client.delete_collection(collection_name)
