import json
from vector_database.srt_splitter import get_splits_from_srt
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4
import chromadb

# Load configuration 
with open('config.json', 'r') as f:
		config = json.load(f)
collection_name=config['collection_name']


def create_vector_database(database_path):
	# Embeddings with Ollama
	embeddings = OllamaEmbeddings(model="llama3")

	# Create vector database with Chroma
	vector_store = Chroma(
		collection_name=collection_name,
		embedding_function=embeddings,
		persist_directory=database_path
	)
	return vector_store

def add_documents_to_database(database_path, splits):
	print("Loading document into database")
	client = chromadb.PersistentClient(path=database_path)
	collection = client.get_or_create_collection(collection_name)
	# Generate ids for the documents
	uuids = [str(uuid4()) for _ in range(len(splits))]
	collection.add(documents=splits, ids=uuids)
	return collection