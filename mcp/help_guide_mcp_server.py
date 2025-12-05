#!/usr/bin/env python3
"""
Help Guide MCP Server - Standalone server for camera help guide search
Completely separate from SDK MCP server
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
from help_guide_search import HelpGuideSearch
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from rate_limiter import RateLimitMiddleware, get_rate_limit_stats

# Load environment variables
load_dotenv()

# Configure logging (force stdout so Railway logs show correct level)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Force stdout instead of stderr for proper Railway log levels
)
logger = logging.getLogger(__name__)

# Create FastMCP server with stateless HTTP
mcp = FastMCP("Help Guide Search Server", stateless_http=True)

# Global help guide search instance
help_guide_search: Optional[HelpGuideSearch] = None

# Connection tracking
active_connections: Dict[str, datetime] = {}
last_heartbeat: datetime = datetime.now()

# Keepalive configuration
KEEPALIVE_INTERVAL = 2.0  # seconds
CONNECTION_TIMEOUT = 10.0  # seconds


@mcp.tool()
def search_help_guides(query: str, top_k: int = 10) -> str:
    """
    Search camera help guides across all models.

    Args:
        query: Natural language search (e.g., "how to use autofocus", "white balance settings")
        top_k: Number of results (default: 10)

    Returns:
        JSON with:
        - results: Array of chunks with content, metadata
        - Each result includes: product_id, help_guide_url, topic/section/subheader context

    Example:
        search_help_guides("eye autofocus")
        → Returns chunks about eye AF from multiple cameras
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        results = help_guide_search.search(query, top_k=top_k)
        results["timestamp"] = datetime.now().isoformat()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Help guide search error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_camera(camera_model: str, query: str, top_k: int = 10) -> str:
    """
    Search within a specific camera's help guide.

    Args:
        camera_model: Camera model (e.g., "ILCE-1M2", "ILME-FR7")
        query: Search query
        top_k: Number of results

    Returns:
        JSON with camera-specific help guide chunks

    Example:
        search_camera("ILCE-1M2", "touch screen settings")
        → Returns ILCE-1M2-specific touch screen docs
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        results = help_guide_search.search_by_camera(camera_model, query, top_k=top_k)
        results["timestamp"] = datetime.now().isoformat()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Camera-specific search error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_topic(topic_title: str, query: str = "", camera_model: Optional[str] = None, top_k: int = 10) -> str:
    """
    Search within a specific topic across cameras.

    Args:
        topic_title: Topic to search (e.g., "Touch function icons", "Shooting")
        query: Optional search query within topic
        camera_model: Optional camera filter
        top_k: Number of results

    Returns:
        JSON with topic-specific chunks

    Example:
        search_topic("Shooting", "burst mode")
        → Returns burst mode info from "Shooting" topic across all cameras

        search_topic("Autofocus", camera_model="ILCE-9M3")
        → Returns all autofocus content for ILCE-9M3
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        results = help_guide_search.search_by_topic(topic_title, query=query, camera_model=camera_model, top_k=top_k)
        results["timestamp"] = datetime.now().isoformat()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Topic search error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def compare_cameras(camera1: str, camera2: str, query: str, top_k: int = 5) -> str:
    """
    Compare two cameras for the same feature or query.

    Args:
        camera1: First camera model (e.g., "ILCE-1M2")
        camera2: Second camera model (e.g., "ILCE-9M3")
        query: Feature to compare (e.g., "autofocus modes", "video recording")
        top_k: Results per camera

    Returns:
        JSON with:
        - camera1_results: Top chunks from camera 1
        - camera2_results: Top chunks from camera 2
        - comparison_note: Guidance for LLM to analyze differences

    Example:
        compare_cameras("ILCE-1M2", "ILCE-9M3", "burst shooting speed")
        → Returns burst shooting specs for both cameras side-by-side
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        results = help_guide_search.compare_cameras(camera1, camera2, query, top_k=top_k)
        results["timestamp"] = datetime.now().isoformat()
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.exception("Camera comparison error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_cameras() -> str:
    """
    Get all cameras with help guides indexed.

    Returns:
        JSON array of camera models with chunk counts

    Example output:
        [
          {"product_id": "ILCE-1M2", "chunk_count": 2811},
          {"product_id": "ILME-FR7", "chunk_count": 1905},
          ...
        ]
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        cameras = help_guide_search.list_cameras()
        return json.dumps({
            "cameras": cameras,
            "total_cameras": len(cameras),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        logger.exception("List cameras error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_topics(camera_model: Optional[str] = None) -> str:
    """
    Get all topics available (optionally filtered by camera).

    Args:
        camera_model: Optional camera filter

    Returns:
        JSON array of unique topic titles

    Example:
        list_topics()
        → Returns all topics across all cameras

        list_topics("ILCE-1M2")
        → Returns topics available in ILCE-1M2 help guide
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        topics = help_guide_search.list_topics(camera_model=camera_model)
        return json.dumps({
            "topics": topics,
            "total_topics": len(topics),
            "camera_filter": camera_model,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    except Exception as e:
        logger.exception("List topics error")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_help_guide_stats() -> str:
    """
    Get help guide index statistics.

    Returns:
        JSON with:
        - total_cameras: 24
        - total_chunks: 55,316
        - chunks_per_camera: {...}
        - index_info: Pinecone index details
    """
    if help_guide_search is None:
        return json.dumps({"error": "Help guide search system not initialized"})

    try:
        stats = help_guide_search.get_stats()
        stats["timestamp"] = datetime.now().isoformat()
        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.exception("Get stats error")
        return json.dumps({"error": str(e)})


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


# Combined lifespan to manage session manager and help guide search initialization
@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    global help_guide_search
    async with contextlib.AsyncExitStack() as stack:
        # Initialize help guide search
        try:
            logger.info("Initializing Help Guide search system...")

            # Check environment variables first
            pinecone_key = os.getenv("PINECONE_API_KEY")
            if not pinecone_key:
                logger.error("PINECONE_API_KEY environment variable not set")
                help_guide_search = None
            else:
                logger.info("PINECONE_API_KEY found, proceeding with Help Guide search initialization...")
                help_guide_search = HelpGuideSearch()
                logger.info("Help Guide search system initialized successfully!")

        except ImportError as e:
            logger.error(f"Missing dependency for help guide search: {e}")
            help_guide_search = None
        except Exception as e:
            logger.exception(f"Failed to initialize help guide search: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            help_guide_search = None

        # Start keepalive task
        keepalive = asyncio.create_task(keepalive_task())

        # Start MCP session manager
        await stack.enter_async_context(mcp.session_manager.run())

        try:
            yield
        finally:
            logger.info("Shutting down server - cleaning up resources...")

            # Cancel keepalive task
            keepalive.cancel()
            try:
                await keepalive
            except asyncio.CancelledError:
                pass

            # Cleanup help guide search instance
            if help_guide_search is not None:
                try:
                    logger.info("Cleaning up help guide search instance...")
                    del help_guide_search
                    logger.info("Help guide search cleanup complete")
                except Exception as e:
                    logger.error(f"Error during help guide search cleanup: {e}")


# Health check endpoint
async def health_check(request):
    """Health check endpoint for Railway and monitoring"""
    status = {
        "status": "healthy",
        "service": "Help Guide Search Server",
        "timestamp": datetime.now().isoformat(),
        "help_guide_search_initialized": help_guide_search is not None,
        "active_connections": len(active_connections),
        "last_heartbeat": last_heartbeat.isoformat()
    }

    # Add help guide stats if initialized
    if help_guide_search is not None:
        try:
            stats = help_guide_search.get_stats()
            status["help_guide_stats"] = {
                "total_cameras": stats.get("total_cameras", 0),
                "total_chunks": stats.get("total_chunks", 0),
                "embedding_model": stats.get("embedding_model", "unknown")
            }
        except Exception as e:
            logger.error(f"Error getting help guide stats for health check: {e}")

    return JSONResponse(status)


# Rate limit stats endpoint
async def rate_limit_stats(request):
    """Rate limit statistics endpoint"""
    stats = get_rate_limit_stats()
    return JSONResponse(stats)


# Create Starlette app with middleware
app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/rate-limit-stats", rate_limit_stats),
    ],
    lifespan=lifespan
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Mount MCP under /mcp
app.mount("/mcp", mcp.streamable_http_app)

# Entry point
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))  # Port 8001 (SDK server uses 8000)

    logger.info(f"Starting Help Guide MCP Server on port {port}")
    logger.info("Endpoints:")
    logger.info(f"  - MCP: http://0.0.0.0:{port}/mcp")
    logger.info(f"  - Health: http://0.0.0.0:{port}/health")
    logger.info(f"  - Rate Limit Stats: http://0.0.0.0:{port}/rate-limit-stats")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
