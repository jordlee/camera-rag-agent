#!/usr/bin/env python3
"""
MCP Server using FastMCP for Claude Web Connector
Official implementation using the Python MCP SDK
"""

import os
import sys
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Add parent directory to path to import search module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP, Context
from search import RAGSearch

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG search instance
rag_search: Optional[RAGSearch] = None

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initialize and cleanup resources"""
    global rag_search
    try:
        logger.info("Initializing RAG search system...")
        rag_search = RAGSearch()
        logger.info("RAG search system initialized successfully!")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize RAG search: {e}")
        yield
    finally:
        logger.info("Shutting down MCP server")

# Create FastMCP server with lifespan management
mcp = FastMCP("SDK RAG Server", lifespan=app_lifespan)

@mcp.tool()
def search_sdk(query: str, top_k: int = 5, content_type: Optional[str] = None) -> str:
    """
    Search the Camera Remote SDK documentation and code examples.
    
    Args:
        query: Search query for SDK information
        top_k: Number of results to return (default: 5)
        content_type: Filter by content type (example_code, documentation_text, documentation_table, function, enum, variable, summary, typedef, define)
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter=content_type)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Error performing search: {str(e)}"

@mcp.tool()
def search_code_examples(query: str, top_k: int = 5) -> str:
    """
    Search specifically for C++ code examples and implementations.
    
    Args:
        query: Search query for C++ code examples
        top_k: Number of results to return (default: 5)
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="example_code")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Code search error: {e}")
        return f"Error searching code examples: {str(e)}"

@mcp.tool()
def search_documentation(query: str, top_k: int = 5) -> str:
    """
    Search SDK documentation text (guides, tutorials, explanations).
    
    Args:
        query: Search query for documentation
        top_k: Number of results to return (default: 5)
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_text")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Documentation search error: {e}")
        return f"Error searching documentation: {str(e)}"

@mcp.tool()
def search_compatibility(query: str, top_k: int = 5) -> str:
    """
    Search camera compatibility tables and structured data.
    
    Args:
        query: Search query for camera compatibility
        top_k: Number of results to return (default: 5)
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="documentation_table")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Compatibility search error: {e}")
        return f"Error searching compatibility: {str(e)}"

@mcp.tool()
def search_api_functions(query: str, top_k: int = 5) -> str:
    """
    Search API function definitions and signatures.
    
    Args:
        query: Search query for API functions
        top_k: Number of results to return (default: 5)
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.search(query, top_k=top_k, content_type_filter="function")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"API function search error: {e}")
        return f"Error searching API functions: {str(e)}"

@mcp.tool()
def get_sdk_stats() -> str:
    """
    Get statistics about the SDK documentation database.
    """
    if rag_search is None:
        return "RAG search system not initialized"
    
    try:
        results = rag_search.get_stats()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return f"Error getting stats: {str(e)}"

# Create ASGI application for deployment
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware.cors import CORSMiddleware

# Mount FastMCP to Starlette for Railway deployment
app = Starlette(
    routes=[
        Mount("/", app=mcp.streamable_http_app()),
    ]
)

# Add CORS middleware for Claude web
app = CORSMiddleware(
    app,
    allow_origins=["https://claude.ai", "*"],  # Allow Claude and all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting FastMCP server on {host}:{port}")
    logger.info("Available tools: search_sdk, search_code_examples, search_documentation, search_compatibility, search_api_functions, get_sdk_stats")
    
    # Run ASGI app with uvicorn for Railway
    uvicorn.run(app, host=host, port=port, log_level="info")