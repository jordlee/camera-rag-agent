#!/usr/bin/env python3
"""
Clear Pinecone Index

Deletes all vectors from the specified Pinecone index.

Usage:
    python scripts/clear_pinecone_index.py
    python scripts/clear_pinecone_index.py --env staging
"""

import os
import argparse
from dotenv import load_dotenv

# Pinecone imports
try:
    from pinecone import Pinecone
except ImportError:
    print("Error: pinecone-client not installed. Run: pip install pinecone-client")
    exit(1)

# Load environment variables
load_dotenv()

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "camera-rag-agent"
PINECONE_HOST = "https://camera-rag-agent-algcc92.svc.aped-4627-b74a.pinecone.io"

# Staging configuration
STAGING_INDEX_NAME = "camera-rag-agent-staging"
STAGING_HOST = "https://camera-rag-agent-staging-algcc92.svc.aped-4627-b74a.pinecone.io"


def clear_index(environment: str = 'production'):
    """Clear all vectors from Pinecone index"""

    # Select index configuration based on environment
    if environment == 'staging':
        index_name = STAGING_INDEX_NAME
        host = STAGING_HOST
    else:
        index_name = PINECONE_INDEX_NAME
        host = PINECONE_HOST

    print(f"Clearing {environment} environment...")
    print(f"  Index: {index_name}")
    print(f"  Host: {host}")

    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable not set")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Connect to index
    index = pc.Index(index_name, host=host)

    # Get index stats before clearing
    stats_before = index.describe_index_stats()
    print(f"\n  Current vectors in index: {stats_before.total_vector_count:,}")

    if stats_before.total_vector_count == 0:
        print("\n✓ Index is already empty")
        return

    # Confirm deletion
    print(f"\n⚠️  WARNING: This will delete all {stats_before.total_vector_count:,} vectors from {index_name}")
    confirmation = input("Type 'DELETE' to confirm: ")

    if confirmation != "DELETE":
        print("Aborted.")
        return

    # Delete all vectors by namespace
    print("\nDeleting all vectors...")

    # Get all namespaces
    namespaces = stats_before.namespaces.keys() if stats_before.namespaces else ['']

    for namespace in namespaces:
        ns_name = namespace if namespace else '(default)'
        print(f"  Clearing namespace: {ns_name}")
        index.delete(delete_all=True, namespace=namespace)

    # Verify deletion
    stats_after = index.describe_index_stats()
    print(f"\n✓ Index cleared!")
    print(f"  Vectors remaining: {stats_after.total_vector_count:,}")


def main():
    parser = argparse.ArgumentParser(description='Clear all vectors from Pinecone index')
    parser.add_argument('--env', '--environment', type=str, default='production',
                        choices=['staging', 'production'],
                        help='Target environment (staging or production)')

    args = parser.parse_args()

    print("=" * 70)
    print("PINECONE INDEX CLEARER")
    print("=" * 70)

    clear_index(environment=args.env)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
