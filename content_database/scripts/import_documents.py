import logging
import os
import sys

from ollama import ResponseError

from content_database.config import settings
from content_database.scripts.vector_database_manager import (
    add_documents_to_vector_database,
)
from llm.llm_manager import LLM_Client


# Only run when executed directly, not when imported as a module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Get the files list from the import folder
    files_list = [
        os.path.join(settings.documents_directory, file)
        for file in os.listdir(settings.documents_directory)
    ]

    # Pick the embedding model from config
    llm_client = LLM_Client()
    embeddings_model = llm_client.get_embeddings_model()

    # Generate or get the database and add the documents on the file list
    try:
        # NOTE: the vector db can use various embedding models. 
        # When adding new docs to the db, the same model must be used. 
        add_documents_to_vector_database(
            settings.database_path, files_list, embeddings_model
        )
    except ResponseError as e:
        print(
            f"\nError: Embedding server returned status {e.status_code}."
            " Is the Ollama server running?",
            file=sys.stderr,
        )
        sys.exit(1)
