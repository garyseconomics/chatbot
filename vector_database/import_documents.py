import os

from config import settings
from vector_database.vector_database_manager import (
    add_documents_to_vector_database,
    delete_existing_collections,
    get_collections_from_database,
)

# Get the files list from the import folder
files_list = [
    os.path.join(settings.documents_directory, file)
    for file in os.listdir(settings.documents_directory)
]


# Gives the option of deleting the existing collections if there are any
def check_and_delete_existing_collections(database_path):
    collections_list = get_collections_from_database(database_path)
    if len(collections_list) > 0:
        answer = input(
            f"There are {len(collections_list)} collections in the database."
            " Delete them before adding new documents? (y/yes): "
        )
        if answer.strip().lower() in ("y", "yes"):
            delete_existing_collections(database_path)


# Check if there is any collections in the database and offer the option to delete them
check_and_delete_existing_collections(settings.database_path)

# Generate or get the database and add the documents on the file list
vector_database = add_documents_to_vector_database(settings.database_path, files_list)
