#!/usr/bin/env python3
"""
FastMCP Server following official SDK examples
For Claude Web Connector
"""

import os
import sys
import json
import logging
import contextlib
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from search import RAGSearch
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

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

@mcp.tool()
def search_sdk(query: str, top_k: int = 5) -> str:
    """Search the Camera Remote SDK documentation and code examples."""
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Search error")
        return f"Error performing search: {str(e)}"

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
        return "RAG search system not initialized"
    
    try:
        results = rag_search.get_stats()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Stats error")
        return f"Error getting stats: {str(e)}"

# Combined lifespan to manage session manager and RAG initialization
@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    global rag_search
    async with contextlib.AsyncExitStack() as stack:
        # Initialize RAG search
        try:
            logger.info("Initializing RAG search system...")
            rag_search = RAGSearch()
            logger.info("RAG search system initialized successfully!")
        except Exception as e:
            logger.exception("Failed to initialize RAG search")
            rag_search = None
        
        # Start MCP session manager
        await stack.enter_async_context(mcp.session_manager.run())
        yield

# Health check endpoint for Railway
async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "fastmcp-server", 
        "rag_initialized": rag_search is not None,
        "mcp_path": "/mcp"
    })

# Create the Starlette app and mount the MCP server - following official example
app = Starlette(
    routes=[
        Route("/health", health_check),
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
    logger.info("Available tools: search_sdk, search_code_examples, search_documentation, search_api_functions, search_compatibility, get_sdk_stats")
    logger.info("Health check: /health")
    logger.info("MCP endpoint: /mcp")
    
    # Run ASGI app with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")