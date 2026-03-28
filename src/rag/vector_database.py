from langchain_chroma import Chroma

from config import settings


def get_vector_database(database_path, embeddings_model):
    # Create vector database with Chroma
    vector_store = Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings_model,
        persist_directory=database_path,
    )
    return vector_store