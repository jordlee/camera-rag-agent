#!/usr/bin/env python3
"""Test script to inspect Pinecone index configuration and sample vectors."""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def inspect_index():
    """Inspect the Pinecone index configuration and sample vectors."""
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "sdk-rag-system")
    index = pc.Index(index_name)
    
    # Get index stats
    stats = index.describe_index_stats()
    print("=" * 80)
    print("Pinecone Index Statistics")
    print("=" * 80)
    print(f"Index name: {index_name}")
    print(f"Total vectors: {stats.get('total_vector_count', 0)}")
    print(f"Dimension: {stats.get('dimension', 'unknown')}")
    print(f"Index fullness: {stats.get('index_fullness', 0):.2%}")
    print(f"Namespaces: {stats.get('namespaces', {})}")
    
    # Query a few random vectors to see metadata
    print("\n" + "=" * 80)
    print("Sample Vector Inspection")
    print("=" * 80)
    
    # Try to fetch some vectors by ID pattern
    sample_ids = [
        "chunk_0", "chunk_1", "chunk_2",  # Try common patterns
        "doc_0", "doc_1", 
        "0", "1", "2"
    ]
    
    try:
        # Fetch vectors
        fetch_result = index.fetch(ids=sample_ids)
        vectors = fetch_result.vectors if hasattr(fetch_result, 'vectors') else {}
        
        if vectors:
            print(f"\nFound {len(vectors)} vectors:")
            for vec_id, vec_data in list(vectors.items())[:3]:
                print(f"\nVector ID: {vec_id}")
                print(f"Metadata: {vec_data.get('metadata', {})}")
                values = vec_data.get('values', [])
                if values:
                    print(f"Vector dimension: {len(values)}")
                    print(f"Vector sample (first 5 values): {values[:5]}")
        else:
            print("No vectors found with common ID patterns")
            
            # Try a query to get some vector IDs
            print("\nTrying a simple query to discover vector IDs...")
            import numpy as np
            random_vector = np.random.randn(768).tolist()  # Assuming 768 dimensions
            
            query_result = index.query(
                vector=random_vector,
                top_k=3,
                include_metadata=True
            )
            
            if query_result.get('matches'):
                print(f"Found {len(query_result['matches'])} matches:")
                for match in query_result['matches']:
                    print(f"\nVector ID: {match.get('id')}")
                    print(f"Score: {match.get('score', 0):.4f}")
                    print(f"Metadata: {match.get('metadata', {})}")
                    
                    # Try to fetch the actual content
                    vec_id = match.get('id')
                    if vec_id:
                        fetch_one = index.fetch(ids=[vec_id])
                        if fetch_one.get('vectors'):
                            vec_data = fetch_one['vectors'][vec_id]
                            print(f"Vector dimension: {len(vec_data.get('values', []))}")
                            
    except Exception as e:
        print(f"Error fetching vectors: {e}")
    
    # Check index configuration
    print("\n" + "=" * 80)
    print("Index Configuration")
    print("=" * 80)
    
    try:
        # Get index description
        index_desc = pc.describe_index(index_name)
        print(f"Metric: {index_desc.get('metric', 'unknown')}")
        print(f"Dimension: {index_desc.get('dimension', 'unknown')}")
        print(f"Spec: {index_desc.get('spec', {})}")
    except Exception as e:
        print(f"Error getting index description: {e}")

if __name__ == "__main__":
    inspect_index()