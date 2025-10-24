import json
from vector_database.srt_splitter import get_splits_from_srt
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import chromadb

# Load configuration 
with open('config.json', 'r') as f:
		config = json.load(f)
collection_name=config['collection_name']
batch_size = config['batch_size']

def get_chromadb_client(database_path):
	client = chromadb.PersistentClient(path=database_path)
	return client

def get_or_create_vector_database(database_path):
	# Embeddings with Ollama
	embeddings = OllamaEmbeddings(model="llama3")

	# Create vector database with Chroma
	vector_store = Chroma(
		collection_name=collection_name,
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
def generate_db_with_documents(database_path, files_list):
	vector_store = get_or_create_vector_database(database_path)
	for filename in files_list:
		print(f"Extracting content from file: {filename}")
		splits = get_splits_from_srt(filename)
		print(f"Obtained {len(splits)} splits of text.")
		for batch in process_in_batches(splits, batch_size):
			print(f"Adding batch: {batch}")
			_ = vector_store.add_documents(documents=batch)
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
