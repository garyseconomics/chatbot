from vector_database.vector_database_manager import get_collections_from_database
from config import database_path


for collection in get_collections_from_database(database_path):
    print(f"Collection name: {collection.name}")
    print(f"Items in the collection: {collection.count()}")
    print(collection.peek())
    print()