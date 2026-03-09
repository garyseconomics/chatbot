import os
from vector_database.vector_database_manager import add_documents_to_vector_database, get_collections_from_database, delete_existing_collections
from config import settings


# Get the files list from the import folder
files_list = [os.path.join(settings.documents_directory, file) for file in os.listdir(settings.documents_directory)]

# Gives the option of deleting the existing collections if there are any
def check_and_delete_existing_collections(database_path):
	collections_list =  get_collections_from_database(database_path)
	if len(collections_list) > 0:
		answer = input(f"There are {len(collections_list)} collections of documents in the database. Do you want to delete them before adding the new documents? (y or yes to confirm): ")
		if answer == "y" or answer == "y" or answer == "Y" or answer == "YES":
			delete_existing_collections(database_path)

# Check if there is any collections in the database and offer the option to delete them
check_and_delete_existing_collections(settings.database_path)

# Generate or get the database and add the documents on the file list
vector_database = add_documents_to_vector_database(settings.database_path, files_list)
