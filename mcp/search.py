"""Pinecone search functionality for the MCP server."""

import os
import re
import time
import asyncio
import logging
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pinecone import Pinecone
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Performance configuration
MAX_EMBEDDING_TIME = 3.0  # Maximum seconds for embedding operation
BATCH_SIZE = 10  # Process queries in small batches
KEEPALIVE_INTERVAL = 2.0  # Send keepalive every 2 seconds
EMBEDDING_CACHE_SIZE = 100  # LRU cache size for embeddings

class CodeBERTEmbedder:
    """Wrapper for CodeBERT model to generate embeddings for code."""
    
    def __init__(self, model_name="microsoft/codebert-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
    
    def encode(self, texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True):
        """Generate embeddings for a list of texts using CodeBERT."""
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize with truncation and padding
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding as the sentence embedding
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            if normalize_embeddings:
                # L2 normalize embeddings
                batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
            
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)

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
        # Using CodeBERT to match the indexing model
        self.embedding_model = CodeBERTEmbedder('microsoft/codebert-base')
        
        # Initialize thread pool for CPU-bound embedding tasks
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Performance tracking
        self.last_embedding_time = 0
        self.total_embeddings_processed = 0
        
        logger.info(f"RAG Search initialized with index: {self.index_name}")
    
    @lru_cache(maxsize=EMBEDDING_CACHE_SIZE)
    def _cached_embed(self, query: str) -> Tuple[float, ...]:
        """Cached embedding generation (tuple for hashability)."""
        # CodeBERT returns numpy array, convert to list then tuple
        embedding = self.embedding_model.encode(query)[0]  # Get first element since we pass single string
        return tuple(embedding.tolist())
    
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
                    'score': match['score'],  # Use actual Pinecone score
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
                    'score': match['score'],  # Use actual Pinecone score
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
                    'score': match['score'],  # Use actual Pinecone score
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
        """Run simplified search strategy - just semantic search with optional filtering."""
        search_tasks = {}
        
        # Primary strategy: Simple semantic search with the expanded query
        search_tasks["semantic"] = self.search_async(query, top_k)
        
        # Optional: If we have a clear category, also do a filtered search
        semantic_categories = intent_context.get("semantic_categories", [])
        if semantic_categories and len(semantic_categories) > 0:
            primary_category = semantic_categories[0]
            content_type = self._map_category_to_content_type(primary_category)
            if content_type:
                search_tasks[f"filtered_{content_type}"] = self.search_async(
                    query, top_k//2, content_type_filter=content_type
                )
        
        # Run searches (simplified - fewer parallel searches)
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
                              intent_context: Dict,  # Keep for compatibility
                              query: str,  # Keep for compatibility
                              top_k: int) -> List[Dict[str, Any]]:
        """
        Fuse results from multiple search strategies and re-rank them.
        
        Now uses actual Pinecone scores without artificial boosting.
        Applies minimum score threshold to filter out poor matches.
        """
        # Minimum score threshold - filter out poor matches
        MIN_SCORE_THRESHOLD = 0.3
        
        # Collect all unique results, keeping the highest natural score
        scored_results = {}
        
        for strategy_name, results in search_results.items():
            for result in results:
                result_id = result.get('id', '')
                if not result_id:
                    continue
                
                # Use the actual Pinecone score
                base_score = result.get('score', 0.0)
                
                # Filter out low-quality results
                if base_score < MIN_SCORE_THRESHOLD:
                    continue
                
                # Keep the highest scoring version of each result (no artificial boosting)
                if result_id not in scored_results or base_score > scored_results[result_id]['score']:
                    scored_results[result_id] = {
                        **result,
                        'score': base_score,  # Use original score field
                        'strategy': strategy_name,
                        'original_score': base_score  # Track for debugging
                    }
        
        # Sort by actual score and return top results
        ranked_results = sorted(
            scored_results.values(), 
            key=lambda x: x['score'], 
            reverse=True
        )
        
        # Log if we filtered out many results
        total_candidates = sum(len(results) for results in search_results.values())
        if len(ranked_results) < total_candidates * 0.5:
            logger.info(f"Filtered {total_candidates - len(ranked_results)} low-scoring results (below {MIN_SCORE_THRESHOLD})")
        
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