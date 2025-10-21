import json
from srt_splitter import get_splits_from_srt
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

def create_vector_database():
	# Get database directory from config file
	with open('config.json', 'r') as f:
		config = json.load(f)
	database_directory = config['database_directory']

	# Embeddings with Ollama
	embeddings = OllamaEmbeddings(model="llama3")

	print("Creating the vector database")
	# Create vector database with Chroma
	vector_store = Chroma(
		embedding_function=embeddings,
		persist_directory=database_directory
	)
	return vector_store

def load_document_into_database(vector_store, filename):
	# Add the documents
	splits = get_splits_from_srt(filename)
	print("Loading document into database")
	_ = vector_store.add_documents(documents=splits)


# Create the database 
vector_store =  create_vector_database()

# Load filename
with open('config.json', 'r') as f:
    config = json.load(f)
filename = config['filename']

# Add the documents
load_document_into_database(vector_store, filename)
