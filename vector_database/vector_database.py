import json
from vector_database.srt_splitter import get_splits_from_srt
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Load configuration 
with open('config.json', 'r') as f:
		config = json.load(f)
database_directory = config['database_directory']
collection_name=config['collection_name']


def create_vector_database():
	# Embeddings with Ollama
	embeddings = OllamaEmbeddings(model="llama3")

	# Create vector database with Chroma
	vector_store = Chroma(
		collection_name=collection_name,
		embedding_function=embeddings,
		persist_directory=database_directory
	)
	return vector_store

def load_document_into_database(vector_store, splits):
	print("Loading document into database")
	_ = vector_store.add_documents(documents=splits)
