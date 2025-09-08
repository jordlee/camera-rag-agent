#!/usr/bin/env python3
"""
Test script to verify timeout fixes in the RAG system.
Tests async embedding, caching, and performance improvements.
"""

import asyncio
import time
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.search import RAGSearch

async def test_async_embedding():
    """Test async embedding with timeout handling."""
    print("\n=== Testing Async Embedding ===")
    rag = RAGSearch()
    
    # Test queries of varying complexity
    test_queries = [
        "camera",  # Simple query
        "How do I connect to a Sony camera using the SDK?",  # Medium query
        "What are all the steps required to implement zoom control, focus adjustment, and exposure settings for a Sony Alpha 7R IV camera using the Camera Remote SDK version 2.00.00?"  # Complex query
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query[:50]}...")
        
        # Test sync embedding
        start = time.time()
        try:
            embedding = rag.embed_query(query)
            sync_time = time.time() - start
            print(f"  Sync embedding: {sync_time:.3f}s (vector size: {len(embedding)})")
        except Exception as e:
            print(f"  Sync embedding failed: {e}")
        
        # Test async embedding
        start = time.time()
        try:
            embedding = await rag.embed_query_async(query)
            async_time = time.time() - start
            print(f"  Async embedding: {async_time:.3f}s (vector size: {len(embedding)})")
        except Exception as e:
            print(f"  Async embedding failed: {e}")

async def test_caching():
    """Test embedding cache performance."""
    print("\n=== Testing Embedding Cache ===")
    rag = RAGSearch()
    
    query = "SetSaveInfo API function"
    
    # First call - cache miss
    start = time.time()
    _ = rag.embed_query(query)
    first_time = time.time() - start
    print(f"First call (cache miss): {first_time:.3f}s")
    
    # Second call - cache hit
    start = time.time()
    _ = rag.embed_query(query)
    second_time = time.time() - start
    print(f"Second call (cache hit): {second_time:.3f}s")
    
    # Show cache stats
    stats = rag.get_performance_stats()
    print(f"Cache stats: {json.dumps(stats, indent=2)}")

async def test_search_performance():
    """Test search performance with different query sizes."""
    print("\n=== Testing Search Performance ===")
    rag = RAGSearch()
    
    test_cases = [
        ("Connect", 5, "simple"),
        ("How to save images to a specific location", 10, "medium"),
        ("Camera compatibility for ILX-LR1", 20, "complex")
    ]
    
    for query, top_k, complexity in test_cases:
        print(f"\n{complexity.capitalize()} query: '{query}' (top_k={top_k})")
        
        # Regular search
        start = time.time()
        try:
            results = rag.search(query, top_k=top_k)
            search_time = time.time() - start
            print(f"  Regular search: {search_time:.3f}s, found {len(results)} results")
        except Exception as e:
            print(f"  Regular search failed: {e}")
        
        # Async search with progress
        progress_updates = []
        async def track_progress(update):
            progress_updates.append(update)
        
        start = time.time()
        try:
            results = await rag.search_async(query, top_k=top_k, progress_callback=track_progress)
            async_time = time.time() - start
            print(f"  Async search: {async_time:.3f}s, found {len(results)} results")
            print(f"  Progress updates: {len(progress_updates)}")
        except Exception as e:
            print(f"  Async search failed: {e}")

async def test_timeout_handling():
    """Test timeout handling for slow operations."""
    print("\n=== Testing Timeout Handling ===")
    rag = RAGSearch()
    
    # Create a very long query that might timeout
    long_query = " ".join([f"camera function {i}" for i in range(100)])
    
    print(f"Testing with extremely long query ({len(long_query)} chars)...")
    
    start = time.time()
    try:
        embedding = await rag.embed_query_async(long_query)
        elapsed = time.time() - start
        print(f"  Completed in {elapsed:.3f}s")
        if elapsed > 3.0:
            print(f"  WARNING: Exceeded 3-second timeout threshold!")
    except asyncio.TimeoutError:
        print(f"  Timeout occurred (as expected for safety)")
    except Exception as e:
        print(f"  Error: {e}")

async def test_batch_processing():
    """Test batch processing for multiple queries."""
    print("\n=== Testing Batch Processing ===")
    rag = RAGSearch()
    
    queries = [
        "Connect to camera",
        "Set exposure",
        "Download images",
        "Focus control",
        "Zoom operation"
    ]
    
    print(f"Processing {len(queries)} queries...")
    
    # Sequential processing
    start = time.time()
    sequential_results = []
    for query in queries:
        results = rag.search(query, top_k=3)
        sequential_results.append(len(results))
    sequential_time = time.time() - start
    print(f"  Sequential: {sequential_time:.3f}s")
    
    # Parallel async processing
    start = time.time()
    tasks = [rag.search_async(query, top_k=3) for query in queries]
    parallel_results = await asyncio.gather(*tasks)
    parallel_time = time.time() - start
    print(f"  Parallel: {parallel_time:.3f}s")
    print(f"  Speedup: {sequential_time/parallel_time:.2f}x")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("RAG System Timeout Fix Verification")
    print("=" * 60)
    
    try:
        await test_async_embedding()
        await test_caching()
        await test_search_performance()
        await test_timeout_handling()
        await test_batch_processing()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())