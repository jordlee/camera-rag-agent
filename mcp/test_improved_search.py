#!/usr/bin/env python3
"""Test the improved search with removed artificial boosting."""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from search import RAGSearch

async def test_improved_search():
    """Test the improved search system with actual Pinecone scores."""
    
    print("=" * 80)
    print("Testing Improved RAG Search (No Artificial Boosting)")
    print("=" * 80)
    
    # Initialize RAG search
    print("\n1. Initializing RAG Search...")
    try:
        rag_search = RAGSearch()
        print("✓ RAG Search initialized successfully")
        print(f"  - Model: CodeBERT (microsoft/codebert-base)")
        print(f"  - Index: {rag_search.index_name}")
        print(f"  - Score threshold: 0.3 (filtering low-quality matches)")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Test queries from FEEDBACK.md
    test_queries = [
        {
            "query": "connect to camera",
            "expected_api": "SCRSDK::Connect",
            "description": "Critical basic query - connection API"
        },
        {
            "query": "save file location",
            "expected_api": "SetSaveInfo",
            "description": "Critical basic query - file operations"
        },
        {
            "query": "get camera settings",
            "expected_api": "GetDeviceProperties",
            "description": "Critical basic query - camera settings"
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
        },
        {
            "query": "zoom control operation",
            "expected_api": "CrDeviceProperty_Zoom_Operation",
            "description": "Synonym query - zoom control"
        }
    ]
    
    print("\n2. Testing queries with improved scoring...")
    print("-" * 80)
    
    all_results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Query: '{test['query']}'")
        print(f"Expected: {test['expected_api']}")
        
        try:
            # Test 1: Regular search (simplified, no boosting)
            print("\n  Regular Search:")
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
                
                print(f"  Top Score: {score:.4f} (raw Pinecone score)")
                print(f"  Type: {metadata.get('type', 'unknown')}")
                
                # Clean up content for display
                content_display = ' '.join(content.split())[:150]
                print(f"  Content: {content_display}...")
                
                # Check if expected API is found
                found_expected = test['expected_api'].lower() in content.lower()
                print(f"  Expected API found: {'✓' if found_expected else '✗'}")
                
                # Show top 3 results with scores
                print("\n  Top 3 results:")
                for j, result in enumerate(results[:3], 1):
                    result_score = result.get('score', 0)
                    result_type = result.get('metadata', {}).get('type', 'unknown')
                    result_content = ' '.join(result.get('content', '').split())[:80]
                    api_found = "✓" if test['expected_api'].lower() in result.get('content', '').lower() else " "
                    print(f"    [{api_found}] #{j}: Score={result_score:.4f}, Type={result_type}")
                    print(f"        {result_content}...")
                
                # Collect results for summary
                all_results.append({
                    'query': test['query'],
                    'expected': test['expected_api'],
                    'top_score': score,
                    'found': found_expected,
                    'filtered_count': len([r for r in results if r.get('score', 0) >= 0.3])
                })
            else:
                print("  ✗ No results returned (all filtered below 0.3 threshold)")
                all_results.append({
                    'query': test['query'],
                    'expected': test['expected_api'],
                    'top_score': 0,
                    'found': False,
                    'filtered_count': 0
                })
            
            # Test 2: Try search_with_intent for comparison
            print("\n  Search with Intent (simplified strategies):")
            intent_results = await rag_search.search_with_intent(
                query=test['query'],
                top_k=5,
                use_intent_mapping=False  # Disable LLM expansion for now
            )
            
            if intent_results and intent_results.get('results'):
                top_intent = intent_results['results'][0]
                intent_score = top_intent.get('score', 0)
                print(f"  Top Score: {intent_score:.4f}")
                print(f"  Strategies used: {intent_results['search_metadata']['search_strategies_used']}")
                
        except Exception as e:
            print(f"  ✗ Search error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    successful = sum(1 for r in all_results if r['found'])
    total = len(all_results)
    
    print(f"\nSuccess rate: {successful}/{total} ({successful/total*100:.1f}%)")
    print("\nScore Analysis:")
    for result in all_results:
        status = "✓" if result['found'] else "✗"
        print(f"  [{status}] '{result['query']}': Score={result['top_score']:.4f}, "
              f"Results after filtering: {result['filtered_count']}")
    
    print("\nKey Changes Applied:")
    print("  1. Removed artificial score boosting (was multiplying by weights)")
    print("  2. Removed hardcoded 1.0 scores for 'exact' matches")
    print("  3. Added 0.3 minimum score threshold to filter poor matches")
    print("  4. Simplified search strategies (reduced from 4+ to 2)")
    print("  5. Using raw Pinecone cosine similarity scores")
    
    print("\nExpected Improvements:")
    print("  - Lower scores overall (no artificial inflation)")
    print("  - Better correlation between score and relevance")
    print("  - Fewer false positives from boosted irrelevant content")
    print("  - Cleaner results after filtering low-score matches")

if __name__ == "__main__":
    asyncio.run(test_improved_search())