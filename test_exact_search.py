#!/usr/bin/env python3
"""Test exact API search functionality with SetSaveInfo."""

import sys
sys.path.append('/Users/jordanlee/Documents/GitHub/sdk-rag-agent/mcp')

from search import RAGSearch

def test_exact_api_search():
    """Test exact API search for SetSaveInfo."""
    print("🔍 Testing exact API search functionality...")
    
    try:
        # Initialize RAG search
        rag = RAGSearch()
        
        # Test 1: Search for SetSaveInfo using exact matching
        print("\n--- Test 1: Exact API Search for 'SetSaveInfo' ---")
        results = rag.search_exact_api("SetSaveInfo", top_k=5)
        print(f"Found {len(results)} exact matches for 'SetSaveInfo'")
        
        if results:
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. Score: {result['score']:.3f}")
                print(f"   Type: {result['metadata'].get('type', 'unknown')}")
                print(f"   Function names: {result['metadata'].get('function_name', [])}")
                print(f"   Content preview: {result['content'][:150]}...")
        else:
            print("❌ No exact matches found - this indicates a problem with metadata filtering")
            
        # Test 2: Compare with semantic search
        print("\n--- Test 2: Semantic Search for 'SetSaveInfo' ---")
        semantic_results = rag.search("SetSaveInfo", top_k=5)
        print(f"Found {len(semantic_results)} semantic matches")
        
        if semantic_results:
            best_semantic = semantic_results[0]
            print(f"Best semantic match score: {best_semantic['score']:.3f}")
            print(f"Content preview: {best_semantic['content'][:100]}...")
            
        # Test 3: Hybrid search
        print("\n--- Test 3: Hybrid Search for 'SetSaveInfo' ---")
        hybrid_results = rag.search_hybrid("SetSaveInfo", top_k=5)
        print(f"Found {len(hybrid_results)} hybrid matches")
        
        # Summary
        print(f"\n--- Summary ---")
        print(f"Exact matches: {len(results)}")
        print(f"Semantic matches: {len(semantic_results)}")
        print(f"Hybrid matches: {len(hybrid_results)}")
        
        if len(results) > 0:
            print("✅ Exact API search is working!")
        else:
            print("❌ Exact API search failed - check metadata format")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_api_search()