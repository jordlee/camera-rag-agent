"""FastAPI MCP Server for Camera Remote SDK RAG System."""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from search import RAGSearch

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Camera Remote SDK RAG System",
    description="MCP Server for Camera Remote SDK documentation and code examples",
    version="1.0.0"
)

# Add CORS middleware for web client support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG search system
try:
    rag_search = RAGSearch()
    logger.info("RAG Search system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG search: {e}")
    rag_search = None

# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    content_type_filter: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int

# MCP Protocol Endpoints
@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Camera Remote SDK RAG System",
        "version": "1.0.0",
        "description": "MCP Server for Camera Remote SDK documentation and code examples",
        "status": "running",
        "endpoints": {
            "search": "/search",
            "search/code": "/search/code", 
            "search/docs": "/search/docs",
            "search/compatibility": "/search/compatibility",
            "search/functions": "/search/functions",
            "health": "/health",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    health_status = rag_search.health_check()
    
    if health_status['status'] == 'healthy':
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)

@app.get("/stats")
async def get_stats():
    """Get index statistics."""
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    return rag_search.get_index_stats()

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    General search endpoint.
    
    Search across all content types in the SDK documentation and code examples.
    """
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    try:
        results = rag_search.search(
            query=request.query,
            top_k=request.top_k,
            content_type_filter=request.content_type_filter
        )
        
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return"),
    type: Optional[str] = Query(None, description="Content type filter")
):
    """
    GET version of search for easy testing and MCP compatibility.
    """
    request = SearchRequest(query=q, top_k=top_k, content_type_filter=type)
    return await search(request)

@app.get("/search/code", response_model=SearchResponse)
async def search_code_examples(
    q: str = Query(..., description="Search query for C++ code examples"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Search specifically for C++ code examples from the SDK.
    
    This endpoint searches through the 229 C++ function implementations,
    static maps, and code structures extracted from the SDK source code.
    """
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    try:
        results = rag_search.search_code_examples(query=q, top_k=top_k)
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            query=q,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Code search error: {e}")
        raise HTTPException(status_code=500, detail=f"Code search failed: {str(e)}")

@app.get("/search/docs", response_model=SearchResponse)
async def search_documentation(
    q: str = Query(..., description="Search query for documentation"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Search specifically for documentation text (2,220 chunks).
    
    This endpoint searches through SDK documentation, guides, and explanatory text.
    """
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    try:
        results = rag_search.search_documentation(query=q, top_k=top_k)
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            query=q,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Documentation search error: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation search failed: {str(e)}")

@app.get("/search/compatibility", response_model=SearchResponse)
async def search_compatibility_tables(
    q: str = Query(..., description="Search query for camera compatibility"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Search camera compatibility tables and structured data (5,230 chunks).
    
    This is the largest content type, containing parameter tables, compatibility matrices, 
    change history, and structured camera compatibility information.
    """
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    try:
        results = rag_search.search_compatibility_tables(query=q, top_k=top_k)
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            query=q,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Compatibility search error: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility search failed: {str(e)}")

@app.get("/search/functions", response_model=SearchResponse)
async def search_api_functions(
    q: str = Query(..., description="Search query for API functions"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Search specifically for API function definitions.
    
    This endpoint searches through API function signatures, parameters, and descriptions.
    """
    if not rag_search:
        raise HTTPException(status_code=503, detail="RAG search system not initialized")
    
    try:
        results = rag_search.search_api_functions(query=q, top_k=top_k)
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            query=q,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Function search error: {e}")
        raise HTTPException(status_code=500, detail=f"Function search failed: {str(e)}")

# MCP Tool Definitions for AI assistants
@app.get("/mcp/tools")
async def get_mcp_tools():
    """
    Return MCP tool definitions for AI assistants.
    
    This endpoint provides the tool schemas that ChatGPT/Claude can use
    to interact with the RAG system.
    """
    return {
        "tools": [
            {
                "name": "search_sdk",
                "description": "Search the Camera Remote SDK documentation and code examples",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for SDK information"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        },
                        "type": {
                            "type": "string",
                            "description": "Content type filter: 'example_code', 'documentation_text', 'function'",
                            "enum": ["example_code", "documentation_text", "function"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_code_examples",
                "description": "Search specifically for C++ code examples and implementations",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for C++ code examples"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_sdk_stats",
                "description": "Get statistics about the SDK documentation database",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # Railway provides PORT dynamically
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,  # Disable in production
        log_level="info"
    )