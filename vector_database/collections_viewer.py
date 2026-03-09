from config import settings
from vector_database.vector_database_manager import get_collections_from_database

for collection in get_collections_from_database(settings.database_path):
    print(f"Collection name: {collection.name}")
    print(f"Items in the collection: {collection.count()}")
    print(collection.peek())
    print()
