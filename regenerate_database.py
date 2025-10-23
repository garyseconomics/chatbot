import json, os
from vector_database.vector_database import generate_db_with_documents, get_collections_from_database, delete_existing_collections

# Load database path from configuration file
with open('config.json', 'r') as f:
		config = json.load(f)
database_path = config['database_directory']
documents_directory = config['documents_directory']

# Get the files list
files_list = [os.path.join(documents_directory, file) for file in os.listdir(documents_directory)]

# Gives the option of deleting the existing collections if there are any
def check_and_delete_existing_collections(database_path):
	collections_list =  get_collections_from_database(database_path)
	if len(collections_list) > 0:
		answer = input(f"There are {len(collections_list)} collections of documents in the database. Do you want to delete them before adding the new documents? (y or yes to confirm): ")
		if answer == "y" or answer == "y" or answer == "Y" or answer == "YES":
			delete_existing_collections(database_path)


# Check if there is any collections in the database and offer the option to delete them
check_and_delete_existing_collections(database_path)

# Generate the database and add the documents on the file list
vector_database = generate_db_with_documents(database_path, files_list)
