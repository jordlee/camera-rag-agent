# scripts/delete_table_chunks.py

import chromadb
from pathlib import Path
import sys

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / "data/chroma_db") 
COLLECTION_NAME = "sdk_docs_local"

def main():
    """
    Connects to the ChromaDB and deletes all entries with the
    metadata type "documentation_table".
    """
    print("--- ChromaDB Deletion Script ---")

    # 1. Connect to the ChromaDB client and collection
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"Successfully connected to collection: '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}", file=sys.stderr)
        print("Please ensure the DB_PATH is correct and the database exists.", file=sys.stderr)
        return

    # 2. Define the filter for the items to be deleted
    deletion_filter = {"type": "documentation_table"}

    # 3. Count the matching entries before deleting (Safety Check)
    try:
        # --- THIS IS THE FIX ---
        # Get the items and count the length of the ID list
        count = len(collection.get(where=deletion_filter)['ids'])
        # --- END FIX ---
        
        print(f"\nFound {count} entries matching the filter: {deletion_filter}")

        if count == 0:
            print("No entries to delete. Exiting.")
            return
            
    except Exception as e:
        print(f"Error counting entries in the collection: {e}", file=sys.stderr)
        return

    # 4. Ask for user confirmation
    confirm = input("Are you sure you want to permanently delete these entries? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled by user.")
        return

    # 5. Perform the deletion
    try:
        print("\nDeleting entries...")
        collection.delete(where=deletion_filter)
        print("Deletion command executed successfully.")
    except Exception as e:
        print(f"An error occurred during deletion: {e}", file=sys.stderr)
        return
        
    # 6. Verify the deletion
    try:
        # --- THIS IS THE FIX ---
        # Verify using the same correct counting method
        final_count = len(collection.get(where=deletion_filter)['ids'])
        # --- END FIX ---

        print(f"Verification: Found {final_count} matching entries after deletion.")
        if final_count == 0:
            print("✅ All specified entries have been successfully removed.")
        else:
            print("⚠️ Verification failed. Some entries may not have been deleted.")
    except Exception as e:
        print(f"Error verifying deletion: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()