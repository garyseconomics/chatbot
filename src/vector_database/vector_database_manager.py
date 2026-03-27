import logging
import time

import chromadb
from langchain_chroma import Chroma

from config import settings
from llm.llm_manager import LLM_Client
from vector_database.srt_splitter import get_splits_from_srt

logger = logging.getLogger(__name__)


def get_chromadb_client(database_path):
    client = chromadb.PersistentClient(path=database_path)
    return client


def get_or_create_vector_database(database_path, embeddings_model):
    # Create vector database with Chroma
    vector_store = Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings_model,
        persist_directory=database_path,
    )
    return vector_store


def process_in_batches(splits, batch_size):
    num_batches = (len(splits) + batch_size - 1) // batch_size
    for i in range(0, len(splits), batch_size):
        logger.info("Batch %d of %d", i // batch_size + 1, num_batches)
        yield splits[i : i + batch_size]


# Creates the database and populates it with the documents provided
def add_documents_to_vector_database(database_path, files_list, embeddings_model=None):
    if not embeddings_model:
        client = LLM_Client()
        embeddings_model = client.get_embeddings_model()
    vector_store = get_or_create_vector_database(database_path, embeddings_model)
    for filename in files_list:
        logger.info("Extracting content from file: %s", filename)
        splits = get_splits_from_srt(filename)
        start_time = time.time()
        logger.debug("Obtained %d splits of text.", len(splits))
        for batch in process_in_batches(splits, settings.batch_size):
            logger.debug("Adding batch: %s", batch)
            current_time = time.time()
            time_processing = current_time - start_time
            now = time.localtime()
            logger.debug(
                "%d:%02d - Time since start: %.2f seconds",
                now.tm_hour,
                now.tm_min,
                time_processing,
            )
            vector_store.add_documents(documents=batch)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info("Total time processing: %.2f seconds", total_time)
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
        logger.info("Deleting collection %s", collection_name)
        client.delete_collection(collection_name)
