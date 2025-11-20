#!/usr/bin/env python3
"""
Unified Embedder for Camera Remote SDK

Handles all SDK variants (Camera Remote, PTP, C#) with a single codebase.
Supports flexible configuration for different index targets and chunk files.
"""

import json
import os
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Pinecone imports - handle SDK version differences
try:
    from pinecone import Pinecone
    from pinecone.grpc import PineconeGRPC
except ImportError:
    from pinecone import Pinecone
    PineconeGRPC = None

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_BATCH_SIZE = 100
DEFAULT_MODEL = "Alibaba-NLP/gte-modernbert-base"
PROJECT_ROOT = Path(__file__).parent.parent.parent


class UnifiedEmbedder:
    """
    Unified embedding system for all SDK variants.

    Example usage:
        embedder = UnifiedEmbedder(
            chunks_file="data/chunks_v2.json",
            index_name="sdk-rag-system-crsdk-v2",
            sdk_type="camera-remote",
            sdk_version="V2.00.00"
        )
        embedder.run()
    """

    def __init__(
        self,
        chunks_file: str,
        index_name: str,
        sdk_type: str = "camera-remote",
        sdk_version: str = "V2.00.00",
        batch_size: int = DEFAULT_BATCH_SIZE,
        model_name: str = DEFAULT_MODEL,
        test_mode: bool = False,
        test_limit: int = 100,
        clear_existing: bool = False,
        environment: str = "production"
    ):
        """
        Initialize unified embedder.

        Args:
            chunks_file: Path to chunks JSON file (relative to project root)
            index_name: Pinecone index name
            sdk_type: SDK type identifier (camera-remote, ptp, csharp)
            sdk_version: SDK version (V1.14.00, V2.00.00, etc.)
            batch_size: Vectors per Pinecone upsert batch
            model_name: SentenceTransformer model name
            test_mode: If True, process only test_limit chunks
            test_limit: Number of chunks to process in test mode
            clear_existing: If True, clear index before uploading
            environment: Target environment (staging or production)
        """
        self.chunks_file = PROJECT_ROOT / chunks_file
        self.environment = environment

        # Override index_name if staging environment
        if environment == "staging":
            self.index_name = "sdk-rag-system-v2-staging"
            print(f"🔧 STAGING MODE: Using staging index: {self.index_name}")
        else:
            self.index_name = index_name

        self.sdk_type = sdk_type
        self.sdk_version = sdk_version
        self.batch_size = batch_size
        self.model_name = model_name
        self.test_mode = test_mode
        self.test_limit = test_limit
        self.clear_existing = clear_existing

        # Get Pinecone API key
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        # State
        self.chunks = []
        self.model = None
        self.index = None
        self.initial_vector_count = 0

    def load_chunks(self):
        """Load chunks from JSON file."""
        print(f"\nLoading chunks from: {self.chunks_file}")

        if not self.chunks_file.exists():
            raise FileNotFoundError(f"Chunk file not found: {self.chunks_file}")

        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)

        print(f"Loaded {len(self.chunks)} chunks")

        # Print chunk type distribution
        type_counts = {}
        for chunk in self.chunks:
            chunk_type = chunk.get('metadata', {}).get('type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

        if type_counts:
            print("\nChunk type distribution:")
            for chunk_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {chunk_type}: {count}")

        # Test mode filtering
        if self.test_mode:
            self.chunks = self.chunks[:self.test_limit]
            print(f"\nTEST MODE: Processing only {len(self.chunks)} chunks")

        return len(self.chunks)

    def init_pinecone(self):
        """Initialize Pinecone connection."""
        print(f"\nConnecting to Pinecone index: {self.index_name}")

        # Use gRPC if available (faster)
        if PineconeGRPC:
            pc = PineconeGRPC(api_key=self.pinecone_api_key)
        else:
            pc = Pinecone(api_key=self.pinecone_api_key)

        # List existing indexes
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        if self.index_name not in existing_indexes:
            raise ValueError(
                f"Index {self.index_name} not found. "
                f"Available indexes: {existing_indexes}"
            )

        print(f"✅ Found index: {self.index_name}")

        # Connect to index
        self.index = pc.Index(self.index_name)

        # Get current stats
        try:
            stats = self.index.describe_index_stats()
            self.initial_vector_count = stats.get('total_vector_count', 0)
            print(f"Current vector count: {self.initial_vector_count:,}")
        except Exception as e:
            print(f"Warning: Could not get stats: {e}")
            self.initial_vector_count = 0

        # Clear index if requested
        if self.clear_existing and self.initial_vector_count > 0:
            print(f"\n🗑️  Clearing existing {self.initial_vector_count:,} vectors...")
            try:
                self.index.delete(delete_all=True)
                print("✅ Index cleared")
                self.initial_vector_count = 0
            except Exception as e:
                print(f"Warning: Could not clear index: {e}")

    def load_model(self):
        """Load embedding model."""
        print(f"\nLoading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.model = self.model.to('cpu')  # Force CPU to avoid memory issues
        print("✅ Model loaded successfully")

    def create_embeddings(self):
        """Create embeddings for all chunks."""
        print(f"\nCreating embeddings for {len(self.chunks)} chunks...")

        texts = [chunk['content'] for chunk in self.chunks]

        start_time = time.time()
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        elapsed = time.time() - start_time
        print(f"Created {len(embeddings)} embeddings in {elapsed:.2f}s")

        return embeddings

    def prepare_vectors(self, embeddings):
        """Prepare vectors for Pinecone upsert."""
        print("\nPreparing vectors for Pinecone...")
        vectors = []

        for chunk, embedding in zip(self.chunks, embeddings):
            # Copy metadata
            metadata = chunk.get('metadata', {}).copy()

            # Add content to metadata (required for retrieval)
            metadata['content'] = chunk['content']

            # Add embedding model info
            metadata['embedding_model'] = self.model_name

            # Add SDK metadata if not present
            if 'sdk_type' not in metadata:
                metadata['sdk_type'] = self.sdk_type
            if 'sdk_version' not in metadata:
                metadata['sdk_version'] = self.sdk_version

            # Sanitize metadata for Pinecone
            sanitized_metadata = self._sanitize_metadata(metadata)

            vectors.append({
                "id": chunk['id'],
                "values": embedding.tolist(),
                "metadata": sanitized_metadata
            })

        print(f"Prepared {len(vectors)} vectors")
        return vectors

    def _sanitize_metadata(self, metadata: dict) -> dict:
        """
        Sanitize metadata for Pinecone compatibility.

        Pinecone supports: strings, numbers, booleans, lists of strings.
        """
        sanitized = {}

        for key, value in metadata.items():
            if value is None:
                sanitized[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Keep arrays as arrays (Pinecone supports this)
                sanitized[key] = value
            elif isinstance(value, dict):
                # Convert nested dicts to JSON strings
                sanitized[key] = json.dumps(value)
            else:
                # Convert other types to strings
                sanitized[key] = str(value)

        return sanitized

    def upsert_vectors(self, vectors):
        """Upsert vectors to Pinecone in batches."""
        print(f"\nUpserting {len(vectors)} vectors to Pinecone...")

        total_upserted = 0
        start_time = time.time()

        for i in range(0, len(vectors), self.batch_size):
            batch = vectors[i:i + self.batch_size]

            try:
                self.index.upsert(vectors=batch)
                total_upserted += len(batch)

                # Progress display
                progress_pct = (total_upserted / len(vectors)) * 100
                elapsed = time.time() - start_time
                rate = total_upserted / elapsed if elapsed > 0 else 0
                eta = (len(vectors) - total_upserted) / rate if rate > 0 else 0

                print(f"  Uploaded {total_upserted}/{len(vectors)} vectors "
                      f"({progress_pct:.1f}%) | Rate: {rate:.1f} vec/s | ETA: {eta:.1f}s",
                      end='\r')
            except Exception as e:
                print(f"\n❌ ERROR upserting batch {i//self.batch_size + 1}: {e}")
                raise

        print(f"\n✅ Successfully upserted {total_upserted} vectors")
        return total_upserted

    def verify_upsert(self, expected_increase):
        """Verify the upsert was successful."""
        print("\nVerifying upsert...")
        time.sleep(3)  # Wait for Pinecone to update stats

        try:
            stats = self.index.describe_index_stats()
            new_count = stats.get('total_vector_count', 0)
            actual_increase = new_count - self.initial_vector_count

            print(f"Before: {self.initial_vector_count:,} vectors")
            print(f"After:  {new_count:,} vectors")
            print(f"Increase: {actual_increase:,} (expected: {expected_increase})")

            if actual_increase == expected_increase:
                print("✅ Verification successful!")
            else:
                print(f"⚠️  Warning: Expected {expected_increase} but got {actual_increase}")
                print("This may be due to Pinecone indexing delay or duplicate IDs.")

            return new_count
        except Exception as e:
            print(f"⚠️  Warning: Could not verify: {e}")
            return self.initial_vector_count + expected_increase

    def run(self):
        """Execute complete embedding pipeline."""
        print("=" * 70)
        print("Unified Embedder - Camera Remote SDK")
        print("=" * 70)
        print(f"SDK Type: {self.sdk_type}")
        print(f"SDK Version: {self.sdk_version}")
        print(f"Index: {self.index_name}")
        print(f"Environment: {self.environment.upper()}")
        print(f"Model: {self.model_name}")
        print(f"Mode: {'TEST' if self.test_mode else 'PRODUCTION'}")
        print("=" * 70)

        # 1. Load chunks
        chunk_count = self.load_chunks()
        if chunk_count == 0:
            print("\n❌ No chunks to process")
            return

        # 2. Connect to Pinecone
        self.init_pinecone()

        # 3. Load embedding model
        self.load_model()

        # 4. Create embeddings
        embeddings = self.create_embeddings()

        # 5. Prepare vectors
        vectors = self.prepare_vectors(embeddings)

        # 6. Upsert to Pinecone
        total_upserted = self.upsert_vectors(vectors)

        # 7. Verify
        final_count = self.verify_upsert(total_upserted)

        # Summary
        print("\n" + "=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(f"SDK Type: {self.sdk_type}")
        print(f"Total chunks embedded: {total_upserted}")
        print(f"Final vector count: {final_count:,}")
        print("=" * 70)


def main():
    """
    Example standalone usage.

    For production use, import UnifiedEmbedder class and configure as needed.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Unified embedder for Camera Remote SDK")
    parser.add_argument("--chunks-file", required=True, help="Path to chunks JSON file (relative to project root)")
    parser.add_argument("--index-name", required=True, help="Pinecone index name")
    parser.add_argument("--sdk-type", default="camera-remote", help="SDK type (camera-remote, ptp, csharp)")
    parser.add_argument("--sdk-version", default="V2.00.00", help="SDK version")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--test", action="store_true", help="Test mode")
    parser.add_argument("--test-limit", type=int, default=100, help="Test mode chunk limit")
    parser.add_argument("--clear", action="store_true", help="Clear existing vectors")
    parser.add_argument("--env", "--environment", type=str, default="production",
                        choices=["staging", "production"],
                        help="Target environment (staging or production). Default: production")

    args = parser.parse_args()

    embedder = UnifiedEmbedder(
        chunks_file=args.chunks_file,
        index_name=args.index_name,
        sdk_type=args.sdk_type,
        sdk_version=args.sdk_version,
        batch_size=args.batch_size,
        model_name=args.model,
        test_mode=args.test,
        test_limit=args.test_limit,
        clear_existing=args.clear,
        environment=args.env
    )

    embedder.run()


if __name__ == "__main__":
    main()
