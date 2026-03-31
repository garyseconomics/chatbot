import logging

from content_database.config import settings
from content_database.scripts.vector_database_manager import (
    delete_existing_collections,
    get_collections_from_database,
)


# Only run when executed directly, not when imported as a module
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    collections_list = get_collections_from_database(settings.database_path)
    if len(collections_list) == 0:
        print("No collections found in the database.")
    else:
        print(f"Collections in the database: {len(collections_list)}")
        for collection in collections_list:
            print(f"  - {collection.name}")
        answer = input("Delete all collections? (y/yes): ")
        if answer.strip().lower() in ("y", "yes"):
            delete_existing_collections(settings.database_path)
            print("Collections deleted.")
        else:
            print("No collections were deleted.")
