"""Pinecone search functionality for the MCP server."""

import os
import re
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Performance configuration
MAX_EMBEDDING_TIME = 3.0  # Maximum seconds for embedding operation
BATCH_SIZE = 10  # Process queries in small batches
KEEPALIVE_INTERVAL = 2.0  # Send keepalive every 2 seconds
EMBEDDING_CACHE_SIZE = 100  # LRU cache size for embeddings

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
        
        # Initialize thread pool for CPU-bound embedding tasks
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Performance tracking
        self.last_embedding_time = 0
        self.total_embeddings_processed = 0
        
        logger.info(f"RAG Search initialized with index: {self.index_name}")
    
    @lru_cache(maxsize=EMBEDDING_CACHE_SIZE)
    def _cached_embed(self, query: str) -> Tuple[float, ...]:
        """Cached embedding generation (tuple for hashability)."""
        return tuple(self.embedding_model.encode(query).tolist())
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query string with caching."""
        try:
            start_time = time.time()
            
            # Use cached embedding if available
            embedding = list(self._cached_embed(query))
            
            elapsed = time.time() - start_time
            self.last_embedding_time = elapsed
            self.total_embeddings_processed += 1
            
            if elapsed > MAX_EMBEDDING_TIME:
                logger.warning(f"Embedding took {elapsed:.2f}s (exceeds {MAX_EMBEDDING_TIME}s limit)")
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def embed_query_async(self, query: str) -> List[float]:
        """Async wrapper for embedding generation with timeout."""
        try:
            loop = asyncio.get_event_loop()
            
            # Run embedding in thread pool with timeout
            future = loop.run_in_executor(self.executor, self.embed_query, query)
            embedding = await asyncio.wait_for(future, timeout=MAX_EMBEDDING_TIME)
            
            return embedding
        except asyncio.TimeoutError:
            logger.error(f"Embedding timeout for query: {query[:50]}...")
            # Return a degraded random embedding as fallback
            import numpy as np
            return np.random.randn(768).tolist()
        except Exception as e:
            logger.error(f"Async embedding error: {e}")
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
    
    async def search_async(self,
                          query: str,
                          top_k: int = 5,
                          content_type_filter: Optional[str] = None,
                          namespace: Optional[str] = None,
                          progress_callback=None) -> List[Dict[str, Any]]:
        """
        Async search with progress updates and timeout handling.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            content_type_filter: Filter by content type
            namespace: Pinecone namespace to search in
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of matching chunks with content and metadata
        """
        try:
            # Step 1: Generate embedding (with progress)
            if progress_callback:
                await progress_callback({"status": "embedding", "progress": 0.3})
            
            query_embedding = await self.embed_query_async(query)
            
            # Step 2: Query Pinecone (with progress)
            if progress_callback:
                await progress_callback({"status": "searching", "progress": 0.6})
            
            # Build filter
            filter_dict = {}
            if content_type_filter:
                filter_dict["type"] = content_type_filter
            
            # Run Pinecone query in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    namespace=namespace,
                    filter=filter_dict if filter_dict else None
                )
            )
            
            # Step 3: Process results (with progress)
            if progress_callback:
                await progress_callback({"status": "processing", "progress": 0.9})
            
            processed_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
                }
                processed_results.append(result)
            
            if progress_callback:
                await progress_callback({"status": "complete", "progress": 1.0})
            
            logger.info(f"Async search found {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            logger.error(f"Async search error: {e}")
            if progress_callback:
                await progress_callback({"status": "error", "error": str(e)})
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_index_stats() for consistency."""
        return self.get_index_stats()
    
    def search_exact_api(self, api_name: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for exact API function names using metadata filtering.
        Addresses the semantic search limitation for specific API names like 'SetSaveInfo'.
        """
        try:
            # Use a generic query vector since we're filtering by metadata
            generic_query = self.embed_query("API function")
            
            # Search with exact metadata filtering
            results = self.index.query(
                vector=generic_query,
                top_k=top_k,
                include_metadata=True,
                filter={
                    "function_name": {"$in": [api_name]}  # Exact match in function_name list
                }
            )
            
            # Process results
            processed_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': 1.0,  # Set high relevance for exact matches
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
                }
                processed_results.append(result)
            
            logger.info(f"Found {len(processed_results)} exact matches for API: {api_name}")
            return processed_results
            
        except Exception as e:
            logger.error(f"Exact API search error: {e}")
            raise
    
    def search_error_codes(self, error_code: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for specific error codes like 'CrError_Connect_TimeOut'."""
        try:
            generic_query = self.embed_query("error code")
            
            results = self.index.query(
                vector=generic_query,
                top_k=top_k,
                include_metadata=True,
                filter={
                    "error_codes": {"$in": [error_code]}
                }
            )
            
            processed_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': 1.0,  # High relevance for exact matches
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
                }
                processed_results.append(result)
            
            logger.info(f"Found {len(processed_results)} matches for error code: {error_code}")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error code search failed: {e}")
            raise
    
    def search_warning_codes(self, warning_code: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for specific warning codes like 'CrWarning_BatteryLow'."""
        try:
            generic_query = self.embed_query("warning code")
            
            results = self.index.query(
                vector=generic_query,
                top_k=top_k,
                include_metadata=True,
                filter={
                    "warning_codes": {"$in": [warning_code]}
                }
            )
            
            processed_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': 1.0,  # High relevance for exact matches
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
                }
                processed_results.append(result)
            
            logger.info(f"Found {len(processed_results)} matches for warning code: {warning_code}")
            return processed_results
            
        except Exception as e:
            logger.error(f"Warning code search failed: {e}")
            raise
    
    def search_hybrid(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining exact API matching with semantic search.
        First tries exact matches, then falls back to semantic search.
        """
        try:
            # Check if query looks like an API name (starts with capital, has specific patterns)
            api_patterns = [
                r'^(Set|Get|Connect|Disconnect|Release|Download)[A-Z]\w*',  # SetSaveInfo, GetDeviceList
                r'^CrDeviceProperty_\w+',  # CrDeviceProperty_*
                r'^CrError_\w+',  # CrError_*
                r'^CrWarning_\w+'  # CrWarning_*
            ]
            
            is_likely_api = any(re.match(pattern, query) for pattern in api_patterns)
            
            if is_likely_api:
                logger.info(f"Query '{query}' appears to be API name, trying exact match first")
                
                # Try exact API search first
                if query.startswith('CrError_'):
                    exact_results = self.search_error_codes(query, top_k//2)
                elif query.startswith('CrWarning_'):
                    exact_results = self.search_warning_codes(query, top_k//2)
                else:
                    exact_results = self.search_exact_api(query, top_k//2)
                
                # If we got exact matches, combine with semantic search for context
                if exact_results:
                    semantic_results = self.search(query, top_k=top_k//2)
                    
                    # Combine results, prioritizing exact matches
                    all_results = exact_results + semantic_results
                    
                    # Remove duplicates by ID
                    seen_ids = set()
                    unique_results = []
                    for result in all_results:
                        if result['id'] not in seen_ids:
                            unique_results.append(result)
                            seen_ids.add(result['id'])
                    
                    return unique_results[:top_k]
            
            # Fallback to regular semantic search
            return self.search(query, top_k)
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fallback to regular search if hybrid fails
            return self.search(query, top_k)

    def health_check(self) -> Dict[str, Any]:
        """Check if the search system is healthy."""
        try:
            # Test with a simple query
            test_results = self.search("camera", top_k=1)
            return {
                'status': 'healthy',
                'pinecone_connected': True,
                'embedding_model_loaded': True,
                'test_query_results': len(test_results),
                'last_embedding_time': self.last_embedding_time,
                'total_embeddings_processed': self.total_embeddings_processed,
                'cache_info': self._cached_embed.cache_info()._asdict()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pinecone_connected': False,
                'embedding_model_loaded': False
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        cache_info = self._cached_embed.cache_info()
        return {
            'last_embedding_time': self.last_embedding_time,
            'total_embeddings_processed': self.total_embeddings_processed,
            'cache_hits': cache_info.hits,
            'cache_misses': cache_info.misses,
            'cache_size': cache_info.currsize,
            'cache_max_size': cache_info.maxsize,
            'cache_hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0
        }
    
    async def search_with_intent(self, 
                                query: str, 
                                top_k: int = 10,
                                use_intent_mapping: bool = True,
                                progress_callback=None) -> Dict[str, Any]:
        """
        Multi-modal search with LLM-based intent mapping.
        
        This is the new primary search method that combines:
        1. LLM intent extraction
        2. Exact API matching
        3. Semantic search
        4. Result fusion and re-ranking
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            use_intent_mapping: Whether to use LLM intent mapping
            progress_callback: Optional progress tracking function
            
        Returns:
            Dictionary with results, intent analysis, and metadata
        """
        start_time = time.time()
        
        if progress_callback:
            await progress_callback({"status": "analyzing_intent", "progress": 0.1})
        
        # Step 1: Query Expansion (instead of intent extraction)
        expanded_query = query
        intent_context = {}
        if use_intent_mapping:
            try:
                # Import here to avoid circular dependency
                from intent_mapper import get_intent_mapper
                mapper = get_intent_mapper()
                expanded_query = await mapper.expand_query_for_search(query)
                
                # Also get some semantic matches for context (but don't use for API generation)
                semantic_matches = await mapper.extract_intent(query)
                intent_context = {
                    "expanded_query": expanded_query,
                    "original_query": query,
                    "expansion_successful": expanded_query != query,
                    "semantic_categories": [match.category for match in semantic_matches[:2]]
                }
                logger.info(f"Query expansion: '{query}' → '{expanded_query}'")
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}")
                expanded_query = query
        
        if progress_callback:
            await progress_callback({"status": "searching", "progress": 0.3})
        
        # Step 2: Multi-modal parallel search with expanded query
        search_results = await self._parallel_search(expanded_query, top_k, intent_context, progress_callback)
        
        if progress_callback:
            await progress_callback({"status": "fusing_results", "progress": 0.8})
        
        # Step 3: Result fusion and re-ranking
        fused_results = self._fuse_and_rank_results(
            search_results, 
            intent_context, 
            query,
            top_k
        )
        
        if progress_callback:
            await progress_callback({"status": "complete", "progress": 1.0})
        
        elapsed = time.time() - start_time
        
        return {
            "results": fused_results[:top_k],
            "intent_analysis": {
                "original_query": query,
                "expanded_query": intent_context.get("expanded_query", query),
                "expansion_successful": intent_context.get("expansion_successful", False),
                "semantic_categories": intent_context.get("semantic_categories", []),
                "llm_expansion_used": use_intent_mapping and intent_context.get("expansion_successful", False)
            },
            "search_metadata": {
                "query": query,
                "expanded_query": intent_context.get("expanded_query", query),
                "total_time": elapsed,
                "search_strategies_used": list(search_results.keys()),
                "total_candidates": sum(len(results) for results in search_results.values())
            },
            "suggestions": self._generate_suggestions(query, intent_context, fused_results)
        }
    
    async def _parallel_search(self, 
                              query: str, 
                              top_k: int, 
                              intent_context: Dict,
                              progress_callback=None) -> Dict[str, List[Dict[str, Any]]]:
        """Run multiple search strategies in parallel using expanded query."""
        search_tasks = {}
        
        # Strategy 1: Enhanced semantic search with expanded query
        search_tasks["semantic_expanded"] = self.search_async(query, top_k//2)
        
        # Strategy 2: Original query search (for comparison/fallback)
        original_query = intent_context.get("original_query", query)
        if original_query != query:
            search_tasks["semantic_original"] = self.search_async(original_query, top_k//3)
        
        # Strategy 3: Content-type specific searches based on semantic categories
        semantic_categories = intent_context.get("semantic_categories", [])
        if semantic_categories:
            primary_category = semantic_categories[0]
            content_type = self._map_category_to_content_type(primary_category)
            if content_type:
                search_tasks[f"category_{primary_category}"] = self.search_async(
                    query, top_k//3, content_type_filter=content_type
                )
        
        # Strategy 4: Keyword-based search (fallback)
        search_tasks["keyword"] = self._keyword_search_async(query, top_k//3)
        
        # Run all searches in parallel
        results = {}
        try:
            search_results = await asyncio.gather(
                *search_tasks.values(),
                return_exceptions=True
            )
            
            for i, (strategy, result) in enumerate(zip(search_tasks.keys(), search_results)):
                if isinstance(result, Exception):
                    logger.error(f"Search strategy {strategy} failed: {result}")
                    results[strategy] = []
                else:
                    results[strategy] = result
                    
        except Exception as e:
            logger.error(f"Parallel search error: {e}")
            # Fallback to regular search
            results["fallback"] = await self.search_async(query, top_k)
        
        return results
    
    async def _search_exact_api_async(self, api_function: str, top_k: int) -> List[Dict[str, Any]]:
        """Async wrapper for exact API search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: self.search_exact_api(api_function, top_k)
        )
    
    async def _keyword_search_async(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based search as fallback."""
        # Extract keywords and search with simple embeddings
        keywords = query.lower().split()
        keyword_query = " ".join(keywords[:5])  # Use first 5 words
        return await self.search_async(keyword_query, top_k)
    
    def _map_category_to_content_type(self, category: str) -> Optional[str]:
        """Map intent categories to content types for targeted search."""
        category_mapping = {
            "connection": "function",
            "file_operations": "function", 
            "camera_settings": "function",
            "focus_control": "function",
            "zoom_control": "function",
            "exposure_control": "function",
            "error_handling": "enum",
        }
        return category_mapping.get(category)
    
    def _fuse_and_rank_results(self, 
                              search_results: Dict[str, List[Dict[str, Any]]], 
                              intent_context: Dict,
                              query: str,
                              top_k: int) -> List[Dict[str, Any]]:
        """
        Fuse results from multiple search strategies and re-rank them.
        
        Uses weighted scoring based on:
        1. Intent confidence
        2. Search strategy reliability
        3. Content relevance score
        4. Result uniqueness
        """
        # Strategy weights (higher = more trustworthy)
        strategy_weights = {
            "semantic_expanded": 1.0,   # Highest weight for LLM-expanded queries
            "semantic_original": 0.8,   # High weight for original semantic search
            "category_": 0.7,           # Good weight for category-specific search
            "keyword": 0.4,             # Lower weight for keyword search
            "fallback": 0.3             # Lowest weight for fallback
        }
        
        # Collect all unique results with weighted scores
        scored_results = {}
        
        for strategy_name, results in search_results.items():
            # Determine strategy weight
            strategy_weight = strategy_weights.get(strategy_name, 0.5)
            for partial_key in strategy_weights.keys():
                if strategy_name.startswith(partial_key):
                    strategy_weight = strategy_weights[partial_key]
                    break
            
            for result in results:
                result_id = result.get('id', '')
                if not result_id:
                    continue
                
                # Calculate composite score
                base_score = result.get('score', 0.0)
                expansion_bonus = 0.0
                
                # Bonus for queries that benefited from expansion
                if intent_context.get("expansion_successful", False):
                    # Give slight bonus to results from expanded queries
                    if strategy_name == "semantic_expanded":
                        expansion_bonus = 0.1
                
                # Final weighted score
                final_score = (base_score * strategy_weight) + expansion_bonus
                
                # Keep the highest scoring version of each result
                if result_id not in scored_results or final_score > scored_results[result_id]['final_score']:
                    scored_results[result_id] = {
                        **result,
                        'final_score': final_score,
                        'strategy': strategy_name,
                        'expansion_bonus': expansion_bonus,
                        'strategy_weight': strategy_weight
                    }
        
        # Sort by final score and return top results
        ranked_results = sorted(
            scored_results.values(), 
            key=lambda x: x['final_score'], 
            reverse=True
        )
        
        return ranked_results
    
    def _generate_suggestions(self, 
                            query: str, 
                            intent_context: Dict,
                            results: List[Dict[str, Any]]) -> List[str]:
        """Generate helpful suggestions for improving queries."""
        suggestions = []
        
        # If query expansion failed or wasn't used
        if not intent_context.get("expansion_successful", False):
            suggestions.extend([
                "Try using more specific technical terms",
                "Include the action you want to perform (e.g., 'connect', 'save', 'set')",
                "Specify the camera component (e.g., 'focus', 'zoom', 'exposure')"
            ])
        
        # If no good matches found even with expansion
        if not results or (results and results[0].get('final_score', 0) < 0.5):
            suggestions.extend([
                "Try breaking your query into simpler parts",
                "Use exact SDK terminology if known"
            ])
        elif intent_context.get("expansion_successful", False):
            # Query expansion worked
            expanded = intent_context.get("expanded_query", "")
            suggestions.append(f"Query was enhanced with terms: {expanded}")
        
        return suggestions[:3]  # Return top 3 suggestions