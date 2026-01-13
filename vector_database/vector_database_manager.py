import os
import time
from dotenv import load_dotenv
from vector_database.srt_splitter import get_splits_from_srt
from langchain_ollama import OllamaEmbeddings
from pydantic import PrivateAttr
from langchain_chroma import Chroma
import chromadb
from langfuse import observe
from config import collection_name, batch_size, show_logs, embedding_model
from llm.langfuse_manager import LangfuseManager


def get_chromadb_client(database_path):
	client = chromadb.PersistentClient(path=database_path)
	return client

class LangfuseOllamaEmbeddings(OllamaEmbeddings):
	_langfuse = PrivateAttr()
	_user_id = PrivateAttr()
	_app_name = PrivateAttr()
	_provider = PrivateAttr()

	def __init__(
		self,
		model,
		user_id="carmen",
		app_name="GarysEconomics_bot",
		provider="ollama-embeddings",
	):
		load_dotenv()
		if not app_name:
			app_name = os.getenv("LANGFUSE_APP_NAME", "GarysEconomics_bot")
		super().__init__(model=model)
		self._langfuse = LangfuseManager()
		self._user_id = user_id
		self._app_name = app_name
		self._provider = provider

	def embed_documents(self, texts):
		try:
			return self._embed_documents_observed(
				texts,
				user_id=self._user_id,
				app_name=self._app_name,
				model_name=self.model,
				provider=self._provider,
			)
		finally:
			self._langfuse.langfuse_client.flush()

	def embed_query(self, text):
		try:
			return self._embed_query_observed(
				text,
				user_id=self._user_id,
				app_name=self._app_name,
				model_name=self.model,
				provider=self._provider,
			)
		finally:
			self._langfuse.langfuse_client.flush()

	@observe(name="ollama_embeddings_documents", as_type="embedding", capture_input=True, capture_output=True)
	def _embed_documents_observed(self, texts, user_id="", app_name="", model_name="", provider=""):
		self._langfuse.langfuse_client.update_current_trace(
			name=app_name,
			user_id=user_id,
			metadata={"model": model_name, "provider": provider},
		)
		return super().embed_documents(texts)

	@observe(name="ollama_embeddings_query", as_type="embedding", capture_input=True, capture_output=True)
	def _embed_query_observed(self, text, user_id="", app_name="", model_name="", provider=""):
		self._langfuse.langfuse_client.update_current_trace(
			name=app_name,
			user_id=user_id,
			metadata={"model": model_name, "provider": provider},
		)
		return super().embed_query(text)

def get_or_create_vector_database(database_path, user_id="", app_name=""):
	# Embeddings with Ollama
	embeddings = LangfuseOllamaEmbeddings(
		model=embedding_model,
		user_id=user_id,
		app_name=app_name,
	)

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
def add_documents_to_vector_database(database_path, files_list):
	vector_store = get_or_create_vector_database(database_path)
	for filename in files_list:
		print(f"Extracting content from file: {filename}")
		splits = get_splits_from_srt(filename)
		start_time = time.time()
		if show_logs:
			print(f"Obtained {len(splits)} splits of text.")
		for batch in process_in_batches(splits, batch_size):
			if show_logs:
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
