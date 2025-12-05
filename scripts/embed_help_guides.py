#!/usr/bin/env python3
"""
Help Guide Embedder for Camera Documentation

Generates embeddings for help guide chunks and uploads to Pinecone.
Uses GTE-ModernBERT model for semantic search.

Usage:
    python scripts/embed_help_guides.py
    python scripts/embed_help_guides.py --input custom_chunks.json
    python scripts/embed_help_guides.py --env staging
"""

import json
import os
import time
import argparse
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Pinecone imports
try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("Error: pinecone-client not installed. Run: pip install pinecone-client")
    exit(1)

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CHUNKS_FILE = PROJECT_ROOT / "data/help-guides-chunks.json"

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "camera-rag-agent"
PINECONE_HOST = "https://camera-rag-agent-algcc92.svc.aped-4627-b74a.pinecone.io"
PINECONE_DIMENSION = 768  # GTE-ModernBERT dimension
PINECONE_METRIC = "cosine"

# Staging configuration
STAGING_INDEX_NAME = "camera-rag-agent-staging"
STAGING_HOST = "https://camera-rag-agent-staging-algcc92.svc.aped-4627-b74a.pinecone.io"

# Model configuration
MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"
BATCH_SIZE = 100  # Pinecone batch size
EMBEDDING_BATCH_SIZE = 32  # Embedding generation batch size


class HelpGuideEmbedder:
    """Generate embeddings and upload to Pinecone"""

    def __init__(self, environment: str = 'production'):
        self.environment = environment

        # Select index configuration based on environment
        if environment == 'staging':
            self.index_name = STAGING_INDEX_NAME
            self.host = STAGING_HOST
        else:
            self.index_name = PINECONE_INDEX_NAME
            self.host = PINECONE_HOST

        print(f"Initializing embedder for {environment} environment...")
        print(f"  Index: {self.index_name}")
        print(f"  Host: {self.host}")

        # Initialize embedding model
        print(f"Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        print("✓ Model loaded")

        # Initialize Pinecone
        self.pc = None
        self.index = None
        self._initialize_pinecone()

        # Statistics
        self.stats = {
            'chunks_processed': 0,
            'embeddings_generated': 0,
            'vectors_uploaded': 0,
            'errors': 0,
            'skipped': 0
        }

    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable not set")

        print(f"\nConnecting to Pinecone index: {self.index_name}")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

        # Check if index exists
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"⚠️  Index '{self.index_name}' does not exist")
            print(f"Available indexes: {existing_indexes}")
            raise ValueError(f"Index '{self.index_name}' not found. Please create it first.")

        # Connect to index
        self.index = self.pc.Index(self.index_name, host=self.host)

        # Get index stats
        stats = self.index.describe_index_stats()
        print(f"✓ Connected to index: {self.index_name}")
        print(f"  Total vectors: {stats.total_vector_count:,}")
        print(f"  Dimension: {stats.dimension}")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts"""
        embeddings = self.model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embeddings

    def prepare_metadata_for_pinecone(self, metadata: Dict) -> Dict:
        """
        Prepare metadata for Pinecone upload
        Pinecone supports: strings, numbers, booleans, lists of strings
        """
        clean_metadata = {}

        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                # Filter out empty/None values and ensure all are strings
                clean_list = [str(v) for v in value if v]
                if clean_list:
                    clean_metadata[key] = clean_list
            else:
                # Convert other types to string
                clean_metadata[key] = str(value)

        return clean_metadata

    def upload_batch(self, vectors: List[tuple]):
        """Upload a batch of vectors to Pinecone"""
        try:
            self.index.upsert(vectors=vectors)
            self.stats['vectors_uploaded'] += len(vectors)
        except Exception as e:
            print(f"  ❌ Error uploading batch: {e}")
            self.stats['errors'] += len(vectors)

    def process_chunks(self, chunks: List[Dict]):
        """Process all chunks: generate embeddings and upload to Pinecone"""
        print(f"\nProcessing {len(chunks)} chunks...")
        print("=" * 70)

        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_idx:batch_idx + BATCH_SIZE]
            batch_num = (batch_idx // BATCH_SIZE) + 1

            print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} chunks)")

            # Extract content for embedding
            texts = [chunk['content'] for chunk in batch]

            # Generate embeddings
            print(f"  Generating embeddings...")
            start_time = time.time()
            embeddings = self.generate_embeddings(texts)
            elapsed = time.time() - start_time
            print(f"  ✓ Generated {len(embeddings)} embeddings in {elapsed:.2f}s")

            self.stats['embeddings_generated'] += len(embeddings)

            # Prepare vectors for Pinecone
            vectors = []
            for i, chunk in enumerate(batch):
                chunk_id = chunk['id']
                embedding = embeddings[i].tolist()
                metadata = self.prepare_metadata_for_pinecone(chunk['metadata'])

                vectors.append((chunk_id, embedding, metadata))

            # Upload to Pinecone
            print(f"  Uploading to Pinecone...")
            self.upload_batch(vectors)
            print(f"  ✓ Uploaded {len(vectors)} vectors")

            self.stats['chunks_processed'] += len(batch)

            # Rate limiting
            time.sleep(0.1)

    def print_stats(self):
        """Print processing statistics"""
        print("\n" + "=" * 70)
        print("EMBEDDING STATISTICS")
        print("=" * 70)
        print(f"Environment: {self.environment.upper()}")
        print(f"Index: {self.index_name}")
        print(f"Chunks processed: {self.stats['chunks_processed']:,}")
        print(f"Embeddings generated: {self.stats['embeddings_generated']:,}")
        print(f"Vectors uploaded: {self.stats['vectors_uploaded']:,}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Skipped: {self.stats['skipped']}")
        print("=" * 70)

        # Get final index stats
        if self.index:
            stats = self.index.describe_index_stats()
            print(f"\nFinal index stats:")
            print(f"  Total vectors in index: {stats.total_vector_count:,}")
            print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Embed camera help guides and upload to Pinecone')
    parser.add_argument('--input', type=str, default=str(DEFAULT_CHUNKS_FILE),
                        help='Input chunks JSON file')
    parser.add_argument('--env', '--environment', type=str, default='production',
                        choices=['staging', 'production'],
                        help='Target environment (staging or production)')

    args = parser.parse_args()

    print("=" * 70)
    print("HELP GUIDE EMBEDDER")
    print("=" * 70)
    print(f"Input: {args.input}")
    print(f"Environment: {args.env.upper()}")
    print(f"Model: {MODEL_NAME}")
    print("=" * 70)

    # Load chunks
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        print(f"Please run chunker first: python scripts/chunk_help_guides.py")
        exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"\n✓ Loaded {len(chunks)} chunks from {input_path}")

    if not chunks:
        print("❌ No chunks to process")
        exit(1)

    # Initialize embedder
    embedder = HelpGuideEmbedder(environment=args.env)

    # Process chunks
    start_time = time.time()
    embedder.process_chunks(chunks)
    total_time = time.time() - start_time

    # Print statistics
    embedder.print_stats()

    print(f"\n⏱️  Total time: {total_time:.2f}s")
    print(f"✅ Embedding complete!")


if __name__ == "__main__":
    main()
