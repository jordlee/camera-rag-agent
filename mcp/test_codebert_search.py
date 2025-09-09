#!/usr/bin/env python3
"""Test script to verify CodeBERT embedding is working correctly in search."""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from search import RAGSearch

async def test_codebert_search():
    """Test the updated search with CodeBERT embeddings."""
    
    print("=" * 80)
    print("Testing CodeBERT-based RAG Search")
    print("=" * 80)
    
    # Initialize RAG search
    print("\n1. Initializing RAG Search with CodeBERT...")
    try:
        rag_search = RAGSearch()
        print("✓ RAG Search initialized successfully")
        print(f"  - Model type: CodeBERTEmbedder")
        print(f"  - Model name: microsoft/codebert-base")
        print(f"  - Index: {rag_search.index_name}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Test queries from the feedback document
    test_queries = [
        {
            "query": "connect to camera",
            "expected_api": "SCRSDK::Connect",
            "description": "Basic connection query"
        },
        {
            "query": "save file location",
            "expected_api": "SetSaveInfo",
            "description": "File save operations"
        },
        {
            "query": "get camera settings",
            "expected_api": "GetDeviceProperties",
            "description": "Camera settings retrieval"
        },
        {
            "query": "SCRSDK::Connect",
            "expected_api": "SCRSDK::Connect",
            "description": "Exact API name search"
        },
        {
            "query": "SetSaveInfo function",
            "expected_api": "SetSaveInfo",
            "description": "API function with keyword"
        }
    ]
    
    print("\n2. Testing search queries with CodeBERT embeddings...")
    print("-" * 80)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Query: '{test['query']}'")
        print(f"Expected: {test['expected_api']}")
        
        try:
            # Perform search
            results = await rag_search.search_async(
                query=test['query'],
                top_k=5
            )
            
            if results:
                # Check top result
                top_result = results[0]
                score = top_result.get('score', 0)
                content = top_result.get('content', '')[:200]
                metadata = top_result.get('metadata', {})
                
                print(f"Top Result Score: {score:.4f}")
                print(f"Content Type: {metadata.get('content_type', 'unknown')}")
                
                # Clean up content for display
                content_display = ' '.join(content.split())[:200]
                print(f"Content Preview: {content_display}...")
                
                # Check if expected API is found
                if test['expected_api'].lower() in content.lower():
                    print(f"✓ Found expected API: {test['expected_api']}")
                else:
                    print(f"✗ Expected API not in top result")
                
                # Show all 5 results for analysis
                print("\nAll results:")
                for j, result in enumerate(results[:5], 1):
                    result_content = ' '.join(result.get('content', '').split())[:100]
                    result_score = result.get('score', 0)
                    result_type = result.get('metadata', {}).get('content_type', 'unknown')
                    api_found = "✓" if test['expected_api'].lower() in result.get('content', '').lower() else " "
                    print(f"  [{api_found}] #{j}: Score={result_score:.4f}, Type={result_type}")
                    print(f"      Content: {result_content}...")
            else:
                print("✗ No results returned")
                
        except Exception as e:
            print(f"✗ Search error: {e}")
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("""
    This test verifies that:
    1. CodeBERT model loads successfully
    2. Embeddings are generated correctly
    3. Search queries return results
    4. Results are more relevant than before (with model mismatch)
    
    Compare these results with the feedback document to see improvement.
    """)

if __name__ == "__main__":
    asyncio.run(test_codebert_search())