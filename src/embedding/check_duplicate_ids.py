# src/embedding/check_duplicate_ids.py

import json
from collections import defaultdict
from pathlib import Path
import sys

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data/chunks.json"

def main():
    """
    Analyzes the chunks.json file to find duplicate IDs and provides an
    option to remove them, keeping only the first occurrence of each ID.
    """
    print("--- Analyzing chunks.json for Duplicate IDs ---")

    try:
        with CHUNKS_FILE.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"Successfully loaded {len(chunks)} chunks from {CHUNKS_FILE}.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading chunks file: {e}", file=sys.stderr)
        return

    # --- Find Duplicates and Prepare Unique List ---
    unique_chunks = []
    seen_ids = set()
    duplicate_count = 0
    
    for chunk in chunks:
        chunk_id = chunk.get('id')
        if chunk_id not in seen_ids:
            unique_chunks.append(chunk)
            seen_ids.add(chunk_id)
        else:
            duplicate_count += 1
            
    print("\n--- Duplicate ID Report ---")
    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicate chunk entries that can be removed.")
        
        # --- Ask for Confirmation Before Deleting ---
        confirm = input("Do you want to permanently remove these duplicates from chunks.json? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled by user. The file has not been changed.")
            return

        # --- Overwrite the File with Clean Data ---
        try:
            with CHUNKS_FILE.open("w", encoding="utf-8") as f:
                json.dump(unique_chunks, f, indent=2)
            
            print(f"\nSuccessfully removed {duplicate_count} duplicates.")
            print(f"The chunks.json file now contains {len(unique_chunks)} unique chunks.")
        except Exception as e:
            print(f"An error occurred while writing the new file: {e}", file=sys.stderr)

    else:
        print("✅ No duplicate IDs found. All chunk IDs are unique.")

if __name__ == "__main__":
    main()