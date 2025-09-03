# scripts/deduplicate_db.py

import chromadb
from pathlib import Path
import sys
from collections import defaultdict

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / "data/chroma_db")
COLLECTION_NAME = "sdk_docs_local"

def main():
    """
    Connects to ChromaDB, finds documents with duplicate IDs,
    and removes the duplicates, keeping only the first instance of each.
    """
    print("--- ChromaDB De-duplication Script ---")

    # 1. Connect to the ChromaDB client and collection
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"Successfully connected to collection: '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}", file=sys.stderr)
        return

    # 2. Retrieve ALL documents from the collection
    try:
        print("\nFetching all documents from the database...")
        # Get all items by not providing any IDs
        all_items = collection.get(include=["metadatas"])
        total_count = len(all_items['ids'])
        print(f"  Found {total_count} total documents.")
    except Exception as e:
        print(f"Error fetching documents: {e}", file=sys.stderr)
        return

    # 3. Identify the duplicates to be deleted
    # Group all document IDs by their metadata 'id' field
    id_to_chroma_ids = defaultdict(list)
    for i, metadata in enumerate(all_items['metadatas']):
        doc_id = metadata.get('id')
        if doc_id:
            # We store the internal ChromaDB ID for later deletion
            id_to_chroma_ids[doc_id].append(all_items['ids'][i])

    # Find which document IDs have more than one entry
    ids_to_delete = []
    duplicate_groups_found = 0
    for doc_id, chroma_ids in id_to_chroma_ids.items():
        if len(chroma_ids) > 1:
            duplicate_groups_found += 1
            # Keep the first one, mark the rest for deletion
            ids_to_delete.extend(chroma_ids[1:])

    print(f"\nAnalysis complete:")
    print(f"  - Found {duplicate_groups_found} unique document IDs with duplicates.")
    print(f"  - A total of {len(ids_to_delete)} chunk entries will be deleted.")

    if not ids_to_delete:
        print("\n✅ No duplicate entries found. Your database is clean.")
        return

    # 4. Ask for user confirmation
    confirm = input("Are you sure you want to permanently delete these duplicate entries? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled by user.")
        return

    # 5. Perform the deletion
    try:
        print(f"\nDeleting {len(ids_to_delete)} entries...")
        # ChromaDB's delete function takes a list of its internal IDs
        collection.delete(ids=ids_to_delete)
        print("Deletion command executed successfully.")
    except Exception as e:
        print(f"An error occurred during deletion: {e}", file=sys.stderr)
        return
        
    # 6. Verify the deletion
    final_count = collection.count()
    expected_count = total_count - len(ids_to_delete)
    print(f"\nVerification:")
    print(f"  - Documents before deletion: {total_count}")
    print(f"  - Documents after deletion: {final_count}")
    print(f"  - Expected documents: {expected_count}")

    if final_count == expected_count:
        print("✅ De-duplication successful.")
    else:
        print("⚠️ Verification failed. The final count does not match the expected count.")

if __name__ == "__main__":
    main()