from content_database.config import settings
from content_database.scripts.vector_database_manager import get_collections_from_database

# Only run when executed directly, not when imported as a module
if __name__ == "__main__":
    for collection in get_collections_from_database(settings.database_path):
        print(f"Collection name: {collection.name}")
        print(f"Items in the collection: {collection.count()}")
        print(collection.peek())
        print()
