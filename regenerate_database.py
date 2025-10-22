import json, os
from vector_database.vector_database import generate_db_with_documents

# Load database path from configuration file
with open('config.json', 'r') as f:
		config = json.load(f)
database_path = config['database_directory']
documents_directory = config['documents_directory']

# Get the files list
files_list = [os.path.join(documents_directory, file) for file in os.listdir(documents_directory)]

# Generate the database
vector_database = generate_db_with_documents(database_path, files_list)
