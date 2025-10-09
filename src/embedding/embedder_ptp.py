#!/usr/bin/env python3
"""
PTP Embedder for Camera Remote SDK V2.00.00-PTP

Processes chunks_ptp_v2.json and upserts to Pinecone index sdk-rag-system-v2-ptp.
Handles all 9 PTP content types with proper metadata preservation.
"""

import json
import os
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Pinecone imports
try:
    from pinecone import Pinecone
    from pinecone.grpc import PineconeGRPC
except ImportError:
    from pinecone import Pinecone
    PineconeGRPC = None

# Load environment variables
load_dotenv()

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
PTP_CHUNKS_FILE = PROJECT_ROOT / "data/chunks_ptp_v2.json"
BATCH_SIZE = 100

# Pinecone configuration (PTP index)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "sdk-rag-system-v2-ptp"  # PTP-specific index

# Model (GTE-ModernBERT for all PTP content)
MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"

# Test mode
TEST_MODE = False  # Set True to process limited chunks
TEST_CHUNK_LIMIT = 100

def load_ptp_chunks():
    """Load PTP chunks from JSON file."""
    print(f"\nLoading PTP chunks from: {PTP_CHUNKS_FILE}")

    if not PTP_CHUNKS_FILE.exists():
        print(f"ERROR: Chunk file not found: {PTP_CHUNKS_FILE}")
        return []

    with open(PTP_CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} PTP chunks")

    # Print chunk type distribution
    type_counts = {}
    for chunk in chunks:
        chunk_type = chunk['metadata'].get('type', 'unknown')
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

    print("\nChunk type distribution:")
    for chunk_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {chunk_type}: {count}")

    if TEST_MODE:
        chunks = chunks[:TEST_CHUNK_LIMIT]
        print(f"\nTEST MODE: Processing only {len(chunks)} chunks")

    return chunks

def init_pinecone():
    """Initialize Pinecone connection to existing PTP index."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment")

    print(f"\nConnecting to Pinecone index: {PINECONE_INDEX_NAME}")

    # Use gRPC if available (faster)
    if PineconeGRPC:
        pc = PineconeGRPC(api_key=PINECONE_API_KEY)
    else:
        pc = Pinecone(api_key=PINECONE_API_KEY)

    # List indexes to verify PTP index exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        raise ValueError(f"Index {PINECONE_INDEX_NAME} not found. Available indexes: {existing_indexes}")

    print(f"✅ Found index: {PINECONE_INDEX_NAME}")

    # Connect to index (let SDK resolve host)
    index = pc.Index(PINECONE_INDEX_NAME)

    # Get current stats
    try:
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        print(f"Current vector count: {total_vectors:,}")
    except Exception as e:
        print(f"Warning: Could not get stats: {e}")
        total_vectors = 0

    return index, total_vectors

def load_embedding_model():
    """Load GTE-ModernBERT model."""
    print(f"\nLoading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    model = model.to('cpu')  # Force CPU to avoid memory issues
    print("Model loaded successfully")
    return model

def create_embeddings(chunks, model):
    """Create embeddings for chunks."""
    print(f"\nCreating embeddings for {len(chunks)} chunks...")

    texts = [chunk['content'] for chunk in chunks]

    start_time = time.time()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    elapsed = time.time() - start_time
    print(f"Created {len(embeddings)} embeddings in {elapsed:.2f}s")

    return embeddings

def prepare_pinecone_vectors(chunks, embeddings):
    """Prepare vectors for Pinecone upsert with PTP-specific metadata."""
    vectors = []

    for chunk, embedding in zip(chunks, embeddings):
        # Copy metadata
        metadata = chunk['metadata'].copy()

        # CRITICAL: Add content to metadata so it can be retrieved during search
        metadata['content'] = chunk['content']

        # Add embedding model info
        metadata['embedding_model'] = MODEL_NAME

        # Handle array fields - convert to comma-separated strings for Pinecone
        if 'function_name' in metadata and isinstance(metadata['function_name'], list):
            metadata['function_name'] = ','.join(metadata['function_name'])

        # Ensure all values are strings, numbers, or booleans
        for key, value in list(metadata.items()):
            if isinstance(value, (list, dict)):
                metadata[key] = str(value)
            elif value is None:
                metadata[key] = ""

        vectors.append({
            "id": chunk['id'],
            "values": embedding.tolist(),
            "metadata": metadata
        })

    return vectors

def upsert_to_pinecone(index, vectors):
    """Upsert vectors to Pinecone in batches."""
    print(f"\nUpserting {len(vectors)} vectors to Pinecone...")

    total_upserted = 0
    start_time = time.time()

    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i:i + BATCH_SIZE]

        try:
            index.upsert(vectors=batch)
            total_upserted += len(batch)

            # Progress display
            progress_pct = (total_upserted / len(vectors)) * 100
            elapsed = time.time() - start_time
            rate = total_upserted / elapsed if elapsed > 0 else 0
            eta = (len(vectors) - total_upserted) / rate if rate > 0 else 0

            print(f"  Progress: {total_upserted}/{len(vectors)} ({progress_pct:.1f}%) | "
                  f"Rate: {rate:.1f} vec/s | ETA: {eta:.1f}s", end='\r')
        except Exception as e:
            print(f"\nERROR upserting batch {i//BATCH_SIZE + 1}: {e}")
            raise

    print(f"\n✅ Successfully upserted {total_upserted} vectors")

    return total_upserted

def verify_upsert(index, initial_count, expected_increase):
    """Verify the upsert was successful."""
    print("\nVerifying upsert...")
    time.sleep(3)  # Wait for Pinecone to update stats

    try:
        stats = index.describe_index_stats()
        new_count = stats.get('total_vector_count', 0)
        actual_increase = new_count - initial_count

        print(f"Before: {initial_count:,} vectors")
        print(f"After:  {new_count:,} vectors")
        print(f"Increase: {actual_increase:,} (expected: {expected_increase})")

        if actual_increase == expected_increase:
            print("✅ Verification successful!")
        else:
            print(f"⚠️  Warning: Expected {expected_increase} but got {actual_increase}")
            print("This may be due to Pinecone indexing delay. Check again in a few moments.")

        return new_count
    except Exception as e:
        print(f"Warning: Could not verify: {e}")
        return initial_count + expected_increase

def main():
    """Main entry point."""
    print("=" * 70)
    print("PTP Embedder for Camera Remote SDK V2.00.00-PTP")
    print("=" * 70)
    print(f"Mode: {'TEST' if TEST_MODE else 'PRODUCTION'}")
    print(f"Index: {PINECONE_INDEX_NAME}")
    print(f"Model: {MODEL_NAME}")
    print("=" * 70)

    # 1. Load chunks
    chunks = load_ptp_chunks()
    if not chunks:
        print("No chunks to process")
        return

    # 2. Connect to Pinecone
    index, initial_count = init_pinecone()

    # 3. Load embedding model
    model = load_embedding_model()

    # 4. Create embeddings
    embeddings = create_embeddings(chunks, model)

    # 5. Prepare vectors
    print("\nPreparing vectors for Pinecone...")
    vectors = prepare_pinecone_vectors(chunks, embeddings)
    print(f"Prepared {len(vectors)} vectors")

    # 6. Upsert to Pinecone
    total_upserted = upsert_to_pinecone(index, vectors)

    # 7. Verify
    final_count = verify_upsert(index, initial_count, total_upserted)

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Total PTP chunks embedded: {total_upserted}")
    print(f"Final vector count: {final_count:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()
