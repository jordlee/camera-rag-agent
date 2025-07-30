# src/embedding/embedder_local.py

import json
from pathlib import Path
import chromadb
import time
import sys
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data/chunks.json"
DB_PATH = PROJECT_ROOT / "data/chroma_db"
COLLECTION_NAME = "sdk_docs_local" # New collection for local embeddings
MODEL_NAME = 'all-MiniLM-L6-v2'    # A fast and effective open-source model
BATCH_SIZE = 64                    # Adjust based on your VRAM/RAM

# --- New: Test Configuration ---
TEST_MODE = False  # Set to True to enable testing on a subset
TEST_CHUNK_LIMIT = 20000  # Number of chunks to process in test mode (adjust as needed)
# You might want to pick a range later if the error is at the end of the file
# For example: TEST_CHUNK_START = 660000; TEST_CHUNK_END = 670000

def format_time(seconds):
    """Converts seconds into a human-readable HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def main():
    """
    Main function to generate embeddings using a local SentenceTransformer model
    and store them in ChromaDB.
    """
    print(f"--- Starting Local Embedding Process ({MODEL_NAME}) ---")

    # 1. Load the chunked data
    print(f"Loading chunks from {CHUNKS_FILE}...")
    try:
        with CHUNKS_FILE.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
        total_chunks = len(chunks)
        print(f"Successfully loaded {total_chunks} chunks.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading chunks file: {e}")
        return

    # --- Apply Test Mode Subset ---
    if TEST_MODE:
        print(f"--- Running in TEST MODE: Processing only {TEST_CHUNK_LIMIT} chunks ---")
        # To test the end, you might use:
        # chunks_to_process = chunks[max(0, total_chunks - TEST_CHUNK_LIMIT):]
        # Or a specific problematic range:
        # chunks_to_process = chunks[TEST_CHUNK_START:TEST_CHUNK_END]
        
        # For general testing, just take the first N chunks:
        chunks_to_process = chunks[max(0, total_chunks - TEST_CHUNK_LIMIT):]
        
        original_total_chunks = total_chunks # Keep track of original total for context
        total_chunks = len(chunks_to_process)
        print(f"Processing {total_chunks} chunks for testing out of {original_total_chunks} total.")
    else:
        chunks_to_process = chunks # Use all chunks if not in test mode

    # 2. Initialize the local SentenceTransformer model
    # Auto-detect the best available device (CUDA > MPS > CPU)
    if torch.cuda.is_available():
        device = 'cuda'
    elif torch.backends.mps.is_available(): # For Apple Silicon
        device = 'mps'
    else:
        device = 'cpu'
    
    print(f"Initializing local model '{MODEL_NAME}' on device '{device}'...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("Model loaded successfully.")

    # 3. Set up the ChromaDB client and collection
    # IMPORTANT: In test mode, you might want to clear the collection first
    # Or use a different collection name to avoid mixing data
    print(f"Setting up ChromaDB at: {DB_PATH}")
    db_client = chromadb.PersistentClient(path=str(DB_PATH))
    
    # Optional: Clear the collection for fresh testing runs
    # if TEST_MODE:
    #     try:
    #         db_client.delete_collection(name=COLLECTION_NAME)
    #         print(f"Cleared existing collection '{COLLECTION_NAME}' for test run.")
    #     except Exception as e:
    #         print(f"Could not clear collection (might not exist): {e}")

    collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"ChromaDB collection '{COLLECTION_NAME}' is ready.")
    
    # 4. Generate embeddings and store in ChromaDB
    start_time = time.time()
    
    # Simple, fixed-size batching for local processing
    # Iterate over 'chunks_to_process' instead of 'chunks'
    for i in range(0, total_chunks, BATCH_SIZE):
        
        batch_chunks = chunks_to_process[i:i + BATCH_SIZE]
        contents = [chunk['content'] for chunk in batch_chunks]
        ids = [chunk['id'] for chunk in batch_chunks]
        metadatas = [chunk['metadata'] for chunk in batch_chunks]

        # Generate embeddings locally.
        embeddings = model.encode(
            contents, 
            show_progress_bar=False,
            normalize_embeddings=True
        )

        collection.add(
            ids=ids,
            embeddings=np.array(embeddings, dtype=np.float32),
            documents=contents,
            metadatas=metadatas
        )

        # Progress Indicator Logic
        processed_chunks = i + len(batch_chunks)
        elapsed_time = time.time() - start_time
        chunks_per_second = processed_chunks / elapsed_time if elapsed_time > 0 else 0
        remaining_chunks = total_chunks - processed_chunks
        etr_seconds = (remaining_chunks / chunks_per_second) if chunks_per_second > 0 else 0
        
        progress_message = (
            f"\rProgress: {(processed_chunks / total_chunks):.2%} | "
            f"Chunks: {processed_chunks}/{total_chunks} | "
            f"Rate: {chunks_per_second:.1f} chunks/sec | "
            f"ETR: {format_time(etr_seconds)}"
        )
        sys.stdout.write(progress_message)
        sys.stdout.flush()

    print(f"\n\n--- Embedding Process Complete ---")
    print(f"All chunks have been embedded and stored in the '{COLLECTION_NAME}' collection.")
    print(f"Total items in collection: {collection.count()}")

if __name__ == "__main__":
    # You may need to install these libraries first:
    # pip install sentence-transformers torch chromadb
    main()