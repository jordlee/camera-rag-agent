#!/usr/bin/env python3
"""
FastMCP Server following official SDK examples
For Claude Web Connector
"""

import os
import sys
import json
import time
import asyncio
import logging
import contextlib
from typing import Optional, Dict
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from search import RAGSearch
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse, StreamingResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server with stateless HTTP - following official example
mcp = FastMCP("SDK RAG Server", stateless_http=True)

# Global RAG search instance
rag_search: Optional[RAGSearch] = None

# Connection tracking
active_connections: Dict[str, datetime] = {}
last_heartbeat: datetime = datetime.now()

# Keepalive configuration
KEEPALIVE_INTERVAL = 2.0  # seconds
CONNECTION_TIMEOUT = 10.0  # seconds

@mcp.tool()
async def search_sdk(query: str, top_k: int = 5) -> str:
    """Search the Camera Remote SDK documentation and code examples using intelligent LLM-based intent mapping and multi-modal search for optimal results."""
    if rag_search is None:
        return json.dumps({"error": "RAG search system not initialized"})
    
    try:
        # Create async progress callback
        async def progress_logger(p):
            logger.info(f"Search progress: {p}")
        
        # Use the new intelligent search with intent mapping
        results = await rag_search.search_with_intent(
            query, 
            top_k=top_k,
            progress_callback=progress_logger
        )
        
        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        
        logger.info(f"Intelligent search completed in {results['search_metadata']['total_time']:.2f}s")
        
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Intelligent search error")
        # Fallback to hybrid search
        try:
            fallback_results = rag_search.search_hybrid(query, top_k=top_k)
            return json.dumps({
                "results": fallback_results,
                "fallback": True,
                "error": f"LLM search failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        except Exception as fallback_error:
            return json.dumps({"error": str(fallback_error)})

@mcp.tool()
def search_code_examples(query: str, top_k: int = 5) -> str:
    """Search specifically for C++ code examples and implementations."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="example_code")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Code search error")
        return f"Error searching code examples: {str(e)}"

@mcp.tool()
def search_documentation(query: str, top_k: int = 5) -> str:
    """Search SDK documentation text (guides, tutorials, explanations)."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_text")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Documentation search error")
        return f"Error searching documentation: {str(e)}"

@mcp.tool()
def search_api_functions(query: str, top_k: int = 5) -> str:
    """Search API function definitions and signatures."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="function")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("API function search error")
        return f"Error searching API functions: {str(e)}"

@mcp.tool()
def search_compatibility(query: str, top_k: int = 5) -> str:
    """Search camera compatibility tables and structured data."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_table")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Compatibility search error")
        return f"Error searching compatibility: {str(e)}"

@mcp.tool()
def get_sdk_stats() -> str:
    """Get statistics about the SDK documentation database."""
    if rag_search is None:
        return json.dumps({"error": "RAG search system not initialized"})
    
    try:
        db_stats = rag_search.get_stats()
        perf_stats = rag_search.get_performance_stats()
        
        combined_stats = {
            "database": db_stats,
            "performance": perf_stats,
            "server": {
                "active_connections": len(active_connections),
                "last_heartbeat": last_heartbeat.isoformat(),
                "uptime_seconds": (datetime.now() - last_heartbeat).total_seconds()
            }
        }
        
        return json.dumps(combined_stats, indent=2)
    except Exception as e:
        logger.exception("Stats error")
        return json.dumps({"error": str(e)})

@mcp.tool()
def search_exact_api(api_name: str, top_k: int = 5) -> str:
    """Search for exact API function names using metadata filtering. Perfect for finding specific functions like 'SetSaveInfo'."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search_exact_api(api_name, top_k=top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Exact API search error")
        return f"Error searching exact API '{api_name}': {str(e)}"

@mcp.tool()
def search_error_codes(error_code: str, top_k: int = 5) -> str:
    """Search for specific error codes like 'CrError_Connect_TimeOut' using exact metadata filtering."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search_error_codes(error_code, top_k=top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Error code search error")
        return f"Error searching error code '{error_code}': {str(e)}"

@mcp.tool()
def search_warning_codes(warning_code: str, top_k: int = 5) -> str:
    """Search for specific warning codes like 'CrWarning_BatteryLow' using exact metadata filtering."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search_warning_codes(warning_code, top_k=top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Warning code search error")
        return f"Error searching warning code '{warning_code}': {str(e)}"

@mcp.tool()
def search_hybrid(query: str, top_k: int = 10) -> str:
    """Smart hybrid search that automatically detects API names, error codes, and other patterns for optimal results."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search_hybrid(query, top_k=top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Hybrid search error")
        return f"Error performing hybrid search for '{query}': {str(e)}"

@mcp.tool()
def search_by_source_file(file_name: str, query: str = "", top_k: int = 5) -> str:
    """Search within a specific source file like 'CameraDevice.cpp' or 'CrDebugString.cpp'."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        # Use advanced filtering with source_file metadata
        generic_query = rag_search.embed_query(query if query else "source code")
        results = rag_search.index.query(
            vector=generic_query,
            top_k=top_k,
            include_metadata=True,
            filter={"source_file": {"$in": [file_name]}}
        )
        
        # Process results in the same format as other functions
        processed_results = []
        for match in results.get('matches', []):
            result = {
                'id': match['id'],
                'score': match['score'],
                'content': match['metadata'].get('content', ''),
                'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'}
            }
            processed_results.append(result)
        
        return json.dumps(processed_results, indent=2)
    except Exception as e:
        logger.exception("Source file search error")
        return f"Error searching in file '{file_name}': {str(e)}"

@mcp.tool() 
async def search_with_intent_analysis(query: str, top_k: int = 10, explain_intent: bool = True) -> str:
    """Advanced search with query expansion using TinyLlama to add related technical terms for better results. Perfect for natural language queries."""
    if rag_search is None:
        return json.dumps({"error": "RAG search system not initialized"})
    
    try:
        # Use full intent-based search with query expansion
        results = await rag_search.search_with_intent(
            query, 
            top_k=top_k,
            use_intent_mapping=True
        )
        
        # Add explanation if requested
        if explain_intent:
            intent_analysis = results.get("intent_analysis", {})
            
            explanation = {
                "query_processing": "Query expanded with related technical terms for better search",
                "original_query": query,
                "expanded_query": intent_analysis.get("expanded_query", query),
                "expansion_successful": intent_analysis.get("expansion_successful", False),
                "terms_added": "Query enhanced with related technical terms" if intent_analysis.get("expansion_successful") else "No expansion performed",
                "semantic_categories": intent_analysis.get("semantic_categories", [])
            }
            results["explanation"] = explanation
        
        results["timestamp"] = datetime.now().isoformat()
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.exception("Query expansion search error")
        return json.dumps({
            "error": str(e),
            "suggestion": "Try a simpler query or use the regular search_sdk tool"
        })

# Keepalive task
async def keepalive_task():
    """Send periodic keepalive messages to maintain connection."""
    global last_heartbeat
    while True:
        try:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            last_heartbeat = datetime.now()
            
            # Clean up stale connections
            now = datetime.now()
            stale_connections = [
                conn_id for conn_id, last_seen in active_connections.items()
                if (now - last_seen).total_seconds() > CONNECTION_TIMEOUT
            ]
            for conn_id in stale_connections:
                del active_connections[conn_id]
                logger.info(f"Removed stale connection: {conn_id}")
            
            # Log heartbeat
            if active_connections:
                logger.debug(f"Heartbeat: {len(active_connections)} active connections")
        except Exception as e:
            logger.error(f"Keepalive error: {e}")

# Combined lifespan to manage session manager and RAG initialization
@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    global rag_search
    async with contextlib.AsyncExitStack() as stack:
        # Initialize RAG search
        try:
            logger.info("Initializing RAG search system...")
            
            # Check environment variables first
            import os
            pinecone_key = os.getenv("PINECONE_API_KEY")
            if not pinecone_key:
                logger.error("PINECONE_API_KEY environment variable not set")
                rag_search = None
            else:
                logger.info("PINECONE_API_KEY found, proceeding with RAG initialization...")
                rag_search = RAGSearch()
                logger.info("RAG search system initialized successfully!")
                
        except ImportError as e:
            logger.error(f"Missing dependency for RAG search: {e}")
            rag_search = None
        except Exception as e:
            logger.exception(f"Failed to initialize RAG search: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            rag_search = None
        
        # Start keepalive task
        keepalive = asyncio.create_task(keepalive_task())
        
        # Start MCP session manager
        await stack.enter_async_context(mcp.session_manager.run())
        
        try:
            yield
        finally:
            # Cancel keepalive task
            keepalive.cancel()
            try:
                await keepalive
            except asyncio.CancelledError:
                pass

# Health check endpoint for Railway
async def health_check(request):
    """Health check endpoint with detailed status."""
    health_status = {
        "status": "healthy",
        "service": "fastmcp-server", 
        "rag_initialized": rag_search is not None,
        "mcp_path": "/mcp",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(active_connections),
        "last_heartbeat": last_heartbeat.isoformat()
    }
    
    # Add performance metrics if available
    if rag_search:
        try:
            perf_stats = rag_search.get_performance_stats()
            health_status["performance"] = {
                "last_embedding_time": perf_stats.get("last_embedding_time", 0),
                "cache_hit_rate": perf_stats.get("cache_hit_rate", 0),
                "total_embeddings": perf_stats.get("total_embeddings_processed", 0)
            }
        except:
            pass
    
    return JSONResponse(health_status)

# SSE endpoint for streaming responses
async def sse_endpoint(request):
    """Server-Sent Events endpoint for streaming responses."""
    async def event_generator():
        connection_id = str(time.time())
        active_connections[connection_id] = datetime.now()
        
        try:
            while True:
                # Send heartbeat
                yield f"data: {{\"type\": \"heartbeat\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
                
                # Update connection timestamp
                active_connections[connection_id] = datetime.now()
                
                await asyncio.sleep(KEEPALIVE_INTERVAL)
        except asyncio.CancelledError:
            # Clean up on disconnect
            if connection_id in active_connections:
                del active_connections[connection_id]
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Create the Starlette app and mount the MCP server - following official example
app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/sse", sse_endpoint),  # SSE endpoint for keepalive
        Mount("/", mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

# Note: Claude web connects to the root URL
# MCP endpoint will be at /mcp automatically by FastMCP

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting FastMCP server on {host}:{port}")
    logger.info("Available tools: search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats, search_exact_api, search_error_codes, search_warning_codes, search_hybrid, search_by_source_file")
    logger.info("Health check: /health")
    logger.info("SSE endpoint: /sse")
    logger.info("MCP endpoint: /mcp")
    logger.info(f"Keepalive interval: {KEEPALIVE_INTERVAL}s")
    logger.info(f"Connection timeout: {CONNECTION_TIMEOUT}s")
    
    # Run ASGI app with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")