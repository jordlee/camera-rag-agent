#!/usr/bin/env python3
"""Migrate ChromaDB embeddings to Pinecone for cloud deployment."""

import os
import json
import chromadb
from pinecone import Pinecone, ServerlessSpec
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data/chroma_db"
COLLECTION_NAME = "sdk_docs_local"

# Pinecone configuration (set these as environment variables)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  # Get from pinecone.io
PINECONE_INDEX_NAME = "sdk-rag-system"
PINECONE_DIMENSION = 768  # All-MPNet dimension
PINECONE_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

def setup_pinecone():
    """Initialize Pinecone and create index if needed."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=PINECONE_DIMENSION,
            metric=PINECONE_METRIC,
            spec=ServerlessSpec(
                cloud=PINECONE_CLOUD,
                region=PINECONE_REGION
            )
        )
        print("✅ Index created successfully")
    else:
        print(f"✅ Using existing index: {PINECONE_INDEX_NAME}")
    
    return pc.Index(PINECONE_INDEX_NAME)

def split_large_chunk(content: str, metadata: dict, chunk_id: str, embedding: list, max_content_size: int = 30000) -> List[Dict[str, Any]]:
    """Split a large chunk into smaller pieces that fit within Pinecone limits."""
    if len(content) <= max_content_size:
        return [{
            'id': chunk_id,
            'values': embedding,
            'metadata': {**metadata, 'content': content}
        }]
    
    # Split content into smaller pieces
    chunks = []
    overlap = 200  # Character overlap between chunks
    
    start = 0
    part_num = 1
    
    while start < len(content):
        end = min(start + max_content_size, len(content))
        
        # Try to break at sentence/line boundaries for better readability
        if end < len(content):
            # Look for good break points (sentence end, line break, etc.)
            for break_char in ['\n\n', '.\n', '. ', '\n']:
                last_break = content.rfind(break_char, start, end)
                if last_break > start + max_content_size // 2:  # Don't break too early
                    end = last_break + len(break_char)
                    break
        
        chunk_content = content[start:end]
        chunk_metadata = metadata.copy()
        chunk_metadata['content'] = chunk_content
        chunk_metadata['chunk_part'] = part_num
        chunk_metadata['total_parts'] = None  # Will be updated after splitting
        
        chunks.append({
            'id': f"{chunk_id}_part{part_num}",
            'values': embedding,  # Reuse same embedding for all parts
            'metadata': chunk_metadata
        })
        
        # Move start position with overlap
        start = max(end - overlap, start + 1)  # Ensure progress
        part_num += 1
    
    # Update total_parts for all chunks
    for chunk in chunks:
        chunk['metadata']['total_parts'] = len(chunks)
    
    return chunks

def export_chromadb_data() -> List[Dict[str, Any]]:
    """Export all data from ChromaDB."""
    print("📦 Connecting to ChromaDB...")
    
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    
    print("📊 Getting collection info...")
    count = collection.count()
    print(f"Found {count} documents in ChromaDB")
    
    print("🔄 Retrieving all documents...")
    results = collection.get(
        include=["documents", "metadatas", "embeddings"]
    )
    
    # Prepare data for Pinecone
    vectors = []
    split_count = 0
    
    print("🔄 Processing and splitting large chunks...")
    for i in range(len(results['ids'])):
        content = results['documents'][i]
        metadata = results['metadatas'][i]
        chunk_id = results['ids'][i]
        embedding = results['embeddings'][i]
        
        # Split if content is too large
        chunk_parts = split_large_chunk(content, metadata, chunk_id, embedding)
        vectors.extend(chunk_parts)
        
        if len(chunk_parts) > 1:
            split_count += 1
    
    print(f"✅ Exported {len(vectors)} vectors from ChromaDB")
    if split_count > 0:
        print(f"📦 Split {split_count} large chunks into multiple parts")
    
    return vectors

def upload_to_pinecone(index, vectors: List[Dict[str, Any]]):
    """Upload vectors to Pinecone in batches."""
    BATCH_SIZE = 100  # Pinecone batch limit
    
    print(f"⬆️ Uploading {len(vectors)} vectors to Pinecone...")
    
    for i in tqdm(range(0, len(vectors), BATCH_SIZE), desc="Uploading batches"):
        batch = vectors[i:i + BATCH_SIZE]
        
        try:
            index.upsert(vectors=batch)
        except Exception as e:
            print(f"❌ Error uploading batch {i//BATCH_SIZE + 1}: {e}")
            raise
    
    print("✅ Upload complete!")

def verify_migration(index, original_count: int):
    """Verify the migration was successful."""
    print("🔍 Verifying migration...")
    
    # Wait a moment for indexing
    import time
    time.sleep(5)
    
    # Get index stats
    stats = index.describe_index_stats()
    pinecone_count = stats['total_vector_count']
    
    print(f"Original ChromaDB count: {original_count}")
    print(f"Pinecone count: {pinecone_count}")
    
    if pinecone_count == original_count:
        print("✅ Migration successful! All vectors uploaded.")
    else:
        print(f"⚠️ Count mismatch. Expected {original_count}, got {pinecone_count}")
    
    return pinecone_count == original_count

def test_search(index):
    """Test a simple search to verify functionality."""
    print("🔬 Testing search functionality...")
    
    # Create a dummy query vector (all zeros)
    query_vector = [0.0] * PINECONE_DIMENSION
    
    try:
        results = index.query(
            vector=query_vector,
            top_k=3,
            include_metadata=True
        )
        
        print(f"✅ Search test successful! Found {len(results['matches'])} results")
        
        if results['matches']:
            print("Sample result:")
            match = results['matches'][0]
            print(f"  ID: {match['id']}")
            print(f"  Score: {match['score']:.4f}")
            print(f"  Type: {match['metadata'].get('type', 'unknown')}")
            print(f"  Content preview: {match['metadata'].get('content', '')[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def main():
    """Main migration process."""
    print("🚀 Starting ChromaDB → Pinecone migration")
    print("=" * 50)
    
    try:
        # Step 1: Setup Pinecone
        index = setup_pinecone()
        
        # Step 2: Export from ChromaDB
        vectors = export_chromadb_data()
        original_count = len(vectors)
        
        # Step 3: Upload to Pinecone
        upload_to_pinecone(index, vectors)
        
        # Step 4: Verify migration
        success = verify_migration(index, original_count)
        
        # Step 5: Test search
        if success:
            test_search(index)
        
        print("=" * 50)
        if success:
            print("🎉 Migration completed successfully!")
            print(f"📍 Your Pinecone index: {PINECONE_INDEX_NAME}")
            print("🔗 Ready for MCP server integration")
        else:
            print("❌ Migration completed with issues")
        
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()