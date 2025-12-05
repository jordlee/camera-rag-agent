"""
Pinecone search functionality for camera help guides.

This module provides semantic search across camera help guide documentation
stored in Pinecone, with support for filtering by camera model and topics.
"""

import os
import time
import logging
import psutil
import traceback
from typing import List, Dict, Any, Optional
from collections import defaultdict
from functools import lru_cache
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Performance configuration
MAX_EMBEDDING_TIME = 3.0
BATCH_SIZE = 32
EMBEDDING_CACHE_SIZE = 100

# Pinecone configuration
PINECONE_INDEX_NAME = "camera-rag-agent"
PINECONE_HOST = "https://camera-rag-agent-algcc92.svc.aped-4627-b74a.pinecone.io"
EMBEDDING_MODEL = "Alibaba-NLP/gte-modernbert-base"
EMBEDDING_DIMENSION = 768


class HelpGuideSearch:
    """Search system for camera help guide documentation."""

    def __init__(self):
        """Initialize the help guide search system."""
        logger.info("=== Starting Help Guide Search Initialization ===")

        # Log system resources
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            logger.info(
                f"System Resources - RAM: {memory.total // (1024**3)}GB "
                f"(Available: {memory.available // (1024**3)}GB), "
                f"Disk: {disk.total // (1024**3)}GB (Free: {disk.free // (1024**3)}GB)"
            )
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")

        # Step 1: Check environment variables
        logger.info("Step 1: Checking environment variables...")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")

        if not self.pinecone_api_key:
            logger.error("PINECONE_API_KEY environment variable not set")
            raise ValueError("PINECONE_API_KEY environment variable not set")
        logger.info("Environment variables OK")

        # Step 2: Initialize Pinecone connection
        logger.info("Step 2: Initializing Pinecone connection...")
        try:
            self.pc = Pinecone(api_key=self.pinecone_api_key)

            logger.info(f"Loading help guide index ({PINECONE_INDEX_NAME})...")
            self.index = self.pc.Index(PINECONE_INDEX_NAME, host=PINECONE_HOST)

            # Get index stats
            stats = self.index.describe_index_stats()
            logger.info(f"✅ Help guide index loaded")
            logger.info(f"   Total vectors: {stats.total_vector_count:,}")
            logger.info(f"   Dimension: {stats.dimension}")

        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            logger.error(f"Pinecone error traceback: {traceback.format_exc()}")
            raise

        # Step 3: Load embedding model
        logger.info(f"Step 3: Loading {EMBEDDING_MODEL} embedding model...")
        try:
            start_time = time.time()

            # Check model cache
            try:
                cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                logger.info(f"HuggingFace cache directory: {cache_dir}")
                if os.path.exists(cache_dir):
                    cache_contents = os.listdir(cache_dir)[:5]
                    logger.info(f"Cache contents (first 5): {cache_contents}")
            except Exception as cache_e:
                logger.warning(f"Could not check cache: {cache_e}")

            logger.info("Creating SentenceTransformer instance...")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

            load_time = time.time() - start_time
            logger.info(f"Model instance created in {load_time:.2f}s, moving to CPU...")

            self.embedding_model = self.embedding_model.to('cpu')

            total_time = time.time() - start_time
            logger.info(f"Embedding model loaded successfully in {total_time:.2f}s")

            # Test the model
            logger.info("Testing model with simple query...")
            test_embedding = self.embedding_model.encode("test query")
            logger.info(f"Test embedding shape: {test_embedding.shape}, type: {type(test_embedding)}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            logger.error(f"Full error traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Could not initialize embedding model: {e}")

        # Step 4: Performance tracking
        logger.info("Step 4: Initializing performance tracking...")
        self.last_embedding_time = 0
        self.total_embeddings_processed = 0
        self.embedding_cache_hits = 0

        logger.info("=== Help Guide Search Initialization Complete ===")
        logger.info(f"✅ Ready to search {stats.total_vector_count:,} help guide chunks")
        logger.info(f"   Model: {EMBEDDING_MODEL}")
        logger.info(f"   Index: {PINECONE_INDEX_NAME}")

        # Log final memory state
        try:
            memory = psutil.virtual_memory()
            logger.info(f"Final memory usage: {memory.percent}% ({memory.used // (1024**3)}GB used)")
        except:
            pass

    @lru_cache(maxsize=EMBEDDING_CACHE_SIZE)
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query string with caching.

        Args:
            query: Search query text

        Returns:
            768-dimensional embedding vector
        """
        start_time = time.time()

        try:
            embedding = self.embedding_model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            self.last_embedding_time = time.time() - start_time
            self.total_embeddings_processed += 1

            if self.last_embedding_time > MAX_EMBEDDING_TIME:
                logger.warning(f"Slow embedding: {self.last_embedding_time:.2f}s for query: {query[:50]}...")

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def search(self, query: str, top_k: int = 10, metadata_filter: Optional[Dict] = None) -> Dict:
        """
        General semantic search across all help guides.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            metadata_filter: Optional Pinecone metadata filter

        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embed_query(query)

            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=metadata_filter
            )

            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                result = {
                    'id': match['id'],
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'metadata': {
                        'product_id': match['metadata'].get('product_id', ''),
                        'help_guide_url': match['metadata'].get('help_guide_url', ''),
                        'page_start': match['metadata'].get('page_start', 0),
                        'page_end': match['metadata'].get('page_end', 0),
                        'topic_title': match['metadata'].get('topic_title', ''),
                        'section_title': match['metadata'].get('section_title', ''),
                        'subheader_title': match['metadata'].get('subheader_title', ''),
                        'hints': match['metadata'].get('hints', []),
                        'related_topics': match['metadata'].get('related_topics', []),
                        'footnotes': match['metadata'].get('footnotes', [])
                    }
                }
                formatted_results.append(result)

            return {
                'results': formatted_results,
                'query': query,
                'top_k': top_k,
                'total_results': len(formatted_results)
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def search_by_camera(self, camera_model: str, query: str, top_k: int = 10) -> Dict:
        """
        Search within a specific camera's help guide.

        Args:
            camera_model: Camera product ID (e.g., "ILCE-1M2", "ILME-FR7")
            query: Search query
            top_k: Number of results

        Returns:
            Dictionary with camera-specific search results
        """
        metadata_filter = {"product_id": camera_model}
        results = self.search(query, top_k=top_k, metadata_filter=metadata_filter)
        results['camera_model'] = camera_model
        return results

    def search_by_topic(self, topic_title: str, query: str = "", camera_model: Optional[str] = None, top_k: int = 10) -> Dict:
        """
        Search within a specific topic across cameras.

        Args:
            topic_title: Topic to search within
            query: Optional search query (if empty, uses topic_title as query)
            camera_model: Optional camera filter
            top_k: Number of results

        Returns:
            Dictionary with topic-filtered search results
        """
        # Build metadata filter - try topic_title first, fall back to section_title
        # Using $or operator to check both fields
        filter_dict = {
            "$or": [
                {"topic_title": topic_title},
                {"section_title": topic_title}
            ]
        }

        # Add camera filter if specified
        if camera_model:
            filter_dict = {
                "$and": [
                    filter_dict,
                    {"product_id": camera_model}
                ]
            }

        # Use topic as query if no query provided
        search_query = query if query else topic_title

        results = self.search(search_query, top_k=top_k, metadata_filter=filter_dict)
        results['topic_title'] = topic_title
        if camera_model:
            results['camera_model'] = camera_model

        return results

    def compare_cameras(self, camera1: str, camera2: str, query: str, top_k: int = 5) -> Dict:
        """
        Compare two cameras for the same feature/query.

        Args:
            camera1: First camera model
            camera2: Second camera model
            query: Feature to compare
            top_k: Results per camera

        Returns:
            Dictionary with side-by-side comparison
        """
        # Search both cameras with the same query
        camera1_results = self.search_by_camera(camera1, query, top_k=top_k)
        camera2_results = self.search_by_camera(camera2, query, top_k=top_k)

        return {
            'query': query,
            'camera1': camera1,
            'camera2': camera2,
            'camera1_results': camera1_results['results'],
            'camera2_results': camera2_results['results'],
            'comparison_note': 'LLM can analyze these results to identify differences and similarities'
        }

    def list_cameras(self) -> List[Dict]:
        """
        Get all available camera models with chunk counts.

        Returns:
            List of dictionaries with product_id and chunk_count
        """
        try:
            # Query a sample to get unique cameras from metadata
            # Use a generic query to get diverse results
            sample_results = self.index.query(
                vector=[0.0] * EMBEDDING_DIMENSION,
                top_k=10000,  # Get large sample
                include_metadata=True
            )

            # Count chunks per camera
            camera_counts = defaultdict(int)
            for match in sample_results.get('matches', []):
                product_id = match['metadata'].get('product_id', 'unknown')
                camera_counts[product_id] += 1

            # Format as list
            cameras = [
                {'product_id': product_id, 'chunk_count': count}
                for product_id, count in sorted(camera_counts.items())
            ]

            return cameras

        except Exception as e:
            logger.error(f"List cameras error: {e}")
            # Return known cameras as fallback
            known_cameras = [
                "BRC-AM7", "DSC-RX0M2", "ILCE-1", "ILCE-1M2", "ILCE-6700",
                "ILCE-7C", "ILCE-7CM2", "ILCE-7CR", "ILCE-7M4", "ILCE-7RM4",
                "ILCE-7RM4A", "ILCE-7RM5", "ILCE-7SM3", "ILCE-9M2", "ILCE-9M3",
                "ILME-FR7", "ILME-FX2", "ILME-FX3", "ILME-FX30", "ILME-FX3A",
                "ILX-LR1", "PXW-Z200, HXR-NX800", "ZV-E1", "ZV-E10M2"
            ]
            return [{'product_id': cam, 'chunk_count': 0} for cam in known_cameras]

    def list_topics(self, camera_model: Optional[str] = None) -> List[str]:
        """
        Get all unique topic titles (optionally filtered by camera).

        Args:
            camera_model: Optional camera filter

        Returns:
            List of unique topic titles
        """
        try:
            # Build filter
            metadata_filter = {"product_id": camera_model} if camera_model else None

            # Query sample
            sample_results = self.index.query(
                vector=[0.0] * EMBEDDING_DIMENSION,
                top_k=10000,
                include_metadata=True,
                filter=metadata_filter
            )

            # Extract unique topics (topic_title or section_title as fallback)
            topics = set()
            for match in sample_results.get('matches', []):
                metadata = match.get('metadata', {})
                topic = metadata.get('topic_title') or metadata.get('section_title')
                if topic and topic.strip():
                    topics.add(topic.strip())

            return sorted(list(topics))

        except Exception as e:
            logger.error(f"List topics error: {e}")
            return []

    def get_stats(self) -> Dict:
        """
        Get help guide index statistics.

        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            cameras = self.list_cameras()

            return {
                'total_cameras': len(cameras),
                'total_chunks': stats.total_vector_count,
                'chunks_per_camera': {cam['product_id']: cam['chunk_count'] for cam in cameras},
                'index_name': PINECONE_INDEX_NAME,
                'embedding_model': EMBEDDING_MODEL,
                'embedding_dimension': EMBEDDING_DIMENSION,
                'performance': {
                    'last_embedding_time': self.last_embedding_time,
                    'total_embeddings_processed': self.total_embeddings_processed,
                    'cache_size': EMBEDDING_CACHE_SIZE
                }
            }
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {'error': str(e)}

    def __del__(self):
        """Cleanup resources on deletion."""
        try:
            logger.info("Cleaning up HelpGuideSearch instance...")
            # Clear embedding cache
            if hasattr(self, 'embed_query'):
                self.embed_query.cache_clear()
            logger.info("HelpGuideSearch cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
