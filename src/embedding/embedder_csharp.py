#!/usr/bin/env python3
"""
C# Embedder for Camera Remote SDK V2.00.00

Processes chunks_csharp_v2.json and upserts to Pinecone.
Does NOT wipe existing data - appends only.
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
CSHARP_CHUNKS_FILE = PROJECT_ROOT / "data/chunks_csharp_v2.json"
BATCH_SIZE = 100

# Pinecone configuration (same V2 index as existing data)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "sdk-rag-system-v2"  # Same index as C++ V2.00.00
PINECONE_HOST = "https://sdk-rag-system-v2-algcc92.svc.aped-4627-b74a.pinecone.io"

# Model (GTE-ModernBERT for C# code)
MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"

# Test mode
TEST_MODE = False  # Set True to process limited chunks
TEST_CHUNK_LIMIT = 10

def load_csharp_chunks():
    """Load C# chunks from JSON file."""
    print(f"\nLoading C# chunks from: {CSHARP_CHUNKS_FILE}")

    if not CSHARP_CHUNKS_FILE.exists():
        print(f"ERROR: Chunk file not found: {CSHARP_CHUNKS_FILE}")
        return []

    with open(CSHARP_CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} C# chunks")

    if TEST_MODE:
        chunks = chunks[:TEST_CHUNK_LIMIT]
        print(f"TEST MODE: Processing only {len(chunks)} chunks")

    return chunks

def init_pinecone():
    """Initialize Pinecone connection."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment")

    print(f"\nConnecting to Pinecone index: {PINECONE_INDEX_NAME}")

    # Use gRPC if available (faster)
    if PineconeGRPC:
        pc = PineconeGRPC(api_key=PINECONE_API_KEY)
    else:
        pc = Pinecone(api_key=PINECONE_API_KEY)

    index = pc.Index(PINECONE_INDEX_NAME, host=PINECONE_HOST)

    # Get current stats
    stats = index.describe_index_stats()
    total_vectors = stats.get('total_vector_count', 0)
    print(f"Current vector count: {total_vectors:,}")

    return index, total_vectors

def load_embedding_model():
    """Load GTE-ModernBERT model."""
    print(f"\nLoading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    model = model.to('cpu')  # Force CPU
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
    """Prepare vectors for Pinecone upsert."""
    vectors = []

    for chunk, embedding in zip(chunks, embeddings):
        # Convert metadata arrays to strings for Pinecone
        metadata = chunk['metadata'].copy()

        # CRITICAL: Add content to metadata so it can be retrieved during search
        metadata['content'] = chunk['content']

        # Handle array fields
        if 'function_name' in metadata and isinstance(metadata['function_name'], list):
            metadata['function_name'] = ','.join(metadata['function_name'])

        if 'sdk_types_used' in metadata and isinstance(metadata['sdk_types_used'], list):
            metadata['sdk_types_used'] = ','.join(metadata['sdk_types_used'][:50])  # Limit size

        # Ensure all values are strings, numbers, or booleans
        for key, value in list(metadata.items()):
            if isinstance(value, (list, dict)):
                metadata[key] = str(value)

        vectors.append({
            "id": chunk['id'],
            "values": embedding.tolist(),
            "metadata": metadata
        })

    return vectors

def delete_csharp_chunks(index):
    """Delete existing C# chunks from Pinecone before re-embedding."""
    print("\n🗑️  Deleting existing C# chunks...")

    try:
        # Query for all C# chunks (using dummy vector since we're filtering by metadata)
        dummy_vector = [0.0] * 768  # GTE-ModernBERT dimension

        # Fetch all C# chunk IDs in batches
        all_csharp_ids = []
        batch_size = 10000

        results = index.query(
            vector=dummy_vector,
            top_k=batch_size,
            include_metadata=True,
            filter={"language": "csharp"}
        )

        for match in results.get('matches', []):
            all_csharp_ids.append(match['id'])

        if not all_csharp_ids:
            print("  No existing C# chunks found")
            return 0

        print(f"  Found {len(all_csharp_ids)} C# chunks to delete")

        # Delete in batches (Pinecone limit is 1000 per delete)
        deleted_count = 0
        delete_batch_size = 1000

        for i in range(0, len(all_csharp_ids), delete_batch_size):
            batch_ids = all_csharp_ids[i:i + delete_batch_size]
            index.delete(ids=batch_ids)
            deleted_count += len(batch_ids)
            print(f"  Deleted {deleted_count}/{len(all_csharp_ids)} chunks", end='\r')

        print(f"\n✅ Deleted {deleted_count} old C# chunks")
        return deleted_count

    except Exception as e:
        print(f"\n⚠️  Warning: Could not delete old chunks: {e}")
        print("  Continuing with upsert (will overwrite existing IDs)...")
        return 0

def upsert_to_pinecone(index, vectors):
    """Upsert vectors to Pinecone in batches."""
    print(f"\nUpserting {len(vectors)} vectors to Pinecone...")

    total_upserted = 0

    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i:i + BATCH_SIZE]

        try:
            index.upsert(vectors=batch)
            total_upserted += len(batch)
            print(f"  Upserted {total_upserted}/{len(vectors)} vectors", end='\r')
        except Exception as e:
            print(f"\nERROR upserting batch {i//BATCH_SIZE + 1}: {e}")
            raise

    print(f"\n✅ Successfully upserted {total_upserted} vectors")

    return total_upserted

def verify_upsert(index, initial_count, expected_increase):
    """Verify the upsert was successful."""
    print("\nVerifying upsert...")
    time.sleep(2)  # Wait for Pinecone to update stats

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

    return new_count

def main():
    """Main entry point."""
    print("=" * 70)
    print("C# Embedder for Camera Remote SDK V2.00.00")
    print("=" * 70)
    print(f"Mode: {'TEST' if TEST_MODE else 'PRODUCTION'}")
    print(f"Index: {PINECONE_INDEX_NAME}")
    print(f"Model: {MODEL_NAME}")
    print("=" * 70)

    # 1. Load chunks
    chunks = load_csharp_chunks()
    if not chunks:
        print("No chunks to process")
        return

    # 2. Connect to Pinecone
    index, initial_count = init_pinecone()

    # 3. Delete existing C# chunks
    deleted_count = delete_csharp_chunks(index)

    # 4. Load embedding model
    model = load_embedding_model()

    # 5. Create embeddings
    embeddings = create_embeddings(chunks, model)

    # 6. Prepare vectors
    print("\nPreparing vectors for Pinecone...")
    vectors = prepare_pinecone_vectors(chunks, embeddings)
    print(f"Prepared {len(vectors)} vectors")

    # 7. Upsert to Pinecone
    total_upserted = upsert_to_pinecone(index, vectors)

    # 8. Verify (expected change = upserted - deleted)
    expected_change = total_upserted - deleted_count
    final_count = verify_upsert(index, initial_count, expected_change)

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Total C# chunks embedded: {total_upserted}")
    print(f"Final vector count: {final_count:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()
