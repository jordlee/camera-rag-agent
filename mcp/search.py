"""Pinecone search functionality for the MCP server."""

import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RAGSearch:
    def __init__(self):
        """Initialize the RAG search system."""
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "sdk-rag-system")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(self.index_name)
        
        # Initialize embedding model (same as used during indexing)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        logger.info(f"RAG Search initialized with index: {self.index_name}")
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query string."""
        try:
            embedding = self.embedding_model.encode(query).tolist()
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def search(self, 
               query: str, 
               top_k: int = 5,
               content_type_filter: Optional[str] = None,
               namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks in Pinecone.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            content_type_filter: Filter by content type (example_code, documentation_text, etc.)
            namespace: Pinecone namespace to search in
            
        Returns:
            List of matching chunks with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embed_query(query)
            
            # Build filter for content type if specified
            filter_dict = {}
            if content_type_filter:
                filter_dict["type"] = content_type_filter
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace,
                filter=filter_dict if filter_dict else None
            )
            
            # Process and return results
            processed_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
                }
                processed_results.append(result)
            
            logger.info(f"Found {len(processed_results)} results for query: {query[:50]}...")
            return processed_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def search_code_examples(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search C++ code examples and implementations (229 chunks).
        
        These are actual C++ function implementations, static maps, and code structures
        extracted from the SDK source code files.
        """
        return self.search(query, top_k=top_k, content_type_filter="example_code")
    
    def search_documentation(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search main documentation text (2,220 chunks).
        
        Includes guides, tutorials, explanatory text, and structured documentation content.
        """
        return self.search(query, top_k=top_k, content_type_filter="documentation_text")
    
    def search_compatibility_tables(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documentation tables for camera compatibility (5,230 chunks).
        
        Parameter tables, compatibility matrices, change history, and structured data.
        This is the largest content type and crucial for camera compatibility information.
        """
        return self.search(query, top_k=top_k, content_type_filter="documentation_table")
    
    def search_api_functions(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search API function definitions (353 chunks).
        
        Function signatures, parameters, and API function documentation.
        """
        return self.search(query, top_k=top_k, content_type_filter="function")
    
    def search_api_properties(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search across all API property types: functions, typedefs, variables, summaries, enums, defines.
        
        This searches the structured API reference content.
        """
        api_types = ["function", "typedef", "variable", "summary", "enum", "define"]
        all_results = []
        results_per_type = max(1, top_k // len(api_types))
        
        for api_type in api_types:
            results = self.search(query, top_k=results_per_type, content_type_filter=api_type)
            all_results.extend(results)
        
        # Sort by relevance score and return top results
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:top_k]
    
    def search_enums(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search enum definitions (528 chunks)."""
        return self.search(query, top_k=top_k, content_type_filter="enum")
    
    def search_typedefs(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search typedef definitions (17 chunks)."""
        return self.search(query, top_k=top_k, content_type_filter="typedef")
    
    def search_variables(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search variable definitions (322 chunks)."""
        return self.search(query, top_k=top_k, content_type_filter="variable")
    
    def search_summaries(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search API summaries (56 chunks)."""
        return self.search(query, top_k=top_k, content_type_filter="summary")
    
    def search_defines(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search preprocessor defines (7 chunks)."""
        return self.search(query, top_k=top_k, content_type_filter="define")
    
    def search_by_category(self, query: str, category: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by content category with smart type selection.
        
        Categories:
        - 'code': Search code examples (229 chunks)
        - 'api': Search API definitions (functions, enums, etc.)  
        - 'docs': Search documentation text (2,220 chunks)
        - 'compatibility': Search compatibility tables (5,230 chunks)
        - 'all': Search everything (8,962 chunks)
        """
        if category == 'code':
            return self.search_code_examples(query, top_k)
        elif category == 'api':
            return self.search_api_properties(query, top_k)
        elif category == 'docs':
            return self.search_documentation(query, top_k)
        elif category == 'compatibility':
            return self.search_compatibility_tables(query, top_k)
        elif category == 'all':
            return self.search(query, top_k)
        else:
            valid_categories = ['code', 'api', 'docs', 'compatibility', 'all']
            raise ValueError(f"Invalid category '{category}'. Valid options: {valid_categories}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        try:
            stats = self.index.describe_index_stats()
            # Convert to dict and extract only serializable values
            stats_dict = dict(stats)
            
            # Extract namespaces info safely
            namespaces_info = {}
            if 'namespaces' in stats_dict and stats_dict['namespaces']:
                for ns_name, ns_data in stats_dict['namespaces'].items():
                    if hasattr(ns_data, 'vector_count'):
                        namespaces_info[ns_name] = {'vector_count': ns_data.vector_count}
                    else:
                        namespaces_info[ns_name] = dict(ns_data) if ns_data else {}
            
            return {
                'total_vectors': stats_dict.get('total_vector_count', 0),
                'dimension': stats_dict.get('dimension', 0),
                'index_fullness': stats_dict.get('index_fullness', 0),
                'namespaces': namespaces_info
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the search system is healthy."""
        try:
            # Test with a simple query
            test_results = self.search("camera", top_k=1)
            return {
                'status': 'healthy',
                'pinecone_connected': True,
                'embedding_model_loaded': True,
                'test_query_results': len(test_results)
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pinecone_connected': False,
                'embedding_model_loaded': False
            }