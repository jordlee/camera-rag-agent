# src/embedding/diagnose_db.py

import chromadb
from pathlib import Path
import os
import sys

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data/chroma_db"
COLLECTION_NAME = "sdk_docs_local"

def main():
    """
    Connects to ChromaDB and provides a diagnostic summary of the collection.
    """
    print("--- ChromaDB Diagnostic Tool ---")

    try:
        # Connect to ChromaDB client and collection
        db_client = chromadb.PersistentClient(path=str(DB_PATH))
        collection = db_client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}", file=sys.stderr)
        print("Please ensure the embedder script has been run and the database exists.", file=sys.stderr)
        return

    # 1. Get total count
    total_count = collection.count()
    print(f"\nTotal items in collection '{COLLECTION_NAME}': {total_count}")
    
    # 2. Get counts for each known metadata type
    # These types are based on your chunker.py script
    known_types = [
        'summary',
        'variable',
        'typedef',
        'enum',
        'api',
        'function',
        'example_code',
        'documentation_text',
        'documentation_table',
        'member' # Including this as it's a fallback in your chunker
    ]
    
    print("\n--- Counts by Metadata Type ---")
    sum_of_filtered_counts = 0
    for type_name in known_types:
        try:
            # Use a get() call with a 'where' filter to get the count
            filtered_count = len(collection.get(where={"type": {"$eq": type_name}})['ids'])
            print(f"  - '{type_name}': {filtered_count} chunks")
            sum_of_filtered_counts += filtered_count
        except Exception as e:
            print(f"  - Error getting count for type '{type_name}': {e}", file=sys.stderr)
    
    print("\n--- Verification ---")
    print(f"Sum of filtered chunks: {sum_of_filtered_counts}")
    if sum_of_filtered_counts == total_count:
        print("✅ Success: The sum of all types matches the total count.")
    else:
        print("⚠️ Warning: The sum of all types does not match the total count.")
        print("  This may indicate missing or miscategorized metadata in your chunks.")

if __name__ == "__main__":
    main()