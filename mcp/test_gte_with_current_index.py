#!/usr/bin/env python3
"""
Test GTE model with current Pinecone index that still has CodeBERT embeddings.
This tests query embedding only - the index still contains CodeBERT vectors.
"""

from search import RAGSearch
from datetime import datetime

# Problematic queries from FEEDBACK.md
PROBLEMATIC_QUERIES = [
    "ILX-LR1",
    "FocalDistanceInMeter", 
    "RemoteCli",
    "65535",
    "CrPriorityKey_PCRemote"
]

def main():
    print("🧪 Testing GTE Query Embeddings with Current (CodeBERT) Index")
    print("=" * 65)
    print("NOTE: Index still contains CodeBERT embeddings, only query embedding uses GTE")
    print()
    
    # Initialize search with GTE query embeddings
    rag = RAGSearch()
    
    for query in PROBLEMATIC_QUERIES:
        print(f"Testing query: '{query}'")
        
        try:
            # Test basic search
            results = rag.search(query, top_k=3)
            
            print(f"  Found {len(results)} results:")
            
            partial_color_found = False
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                content = result.get('content', '')[:100].replace('\n', ' ').strip()
                
                if 'Partial Color Yellow' in result.get('content', ''):
                    partial_color_found = True
                    content = "🚨 PARTIAL COLOR YELLOW " + content
                
                print(f"    {i}. Score: {score:.4f} - {content}...")
            
            if partial_color_found:
                print("    ❌ Still returning 'Partial Color Yellow'")
            else:
                print("    ✅ No 'Partial Color Yellow' in results")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        print()
    
    print("NOTE: Since the index still contains CodeBERT embeddings, we expect")
    print("mixed results. Full improvement requires re-indexing with GTE.")

if __name__ == "__main__":
    main()