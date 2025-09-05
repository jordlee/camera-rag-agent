# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) system for Camera Remote SDK documentation. The system parses SDK documentation from multiple sources (HTML, PDF, XML, C++ headers), chunks the content, creates embeddings, and provides an intelligent query interface.

## Development Commands

### Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Core Pipeline Commands
```bash
# 1. Parse documentation from raw sources
python src/parsing/pdf_parser.py      # Parse PDF documentation
python src/parsing/html_parser.py     # Parse HTML API docs
python src/parsing/cpp_parser.py      # Parse C++ headers with Doxygen
python src/parsing/markdown_parser.py # Parse markdown files
python src/parsing/rst_parser.py      # Parse RST files

# 2. Chunk the parsed content
python src/parsing/chunker.py

# 3. Generate embeddings and store in ChromaDB
python src/embedding/embedder_local.py

# 4. Query the RAG system
python src/rag/query_system.py
```

### Diagnostics and Maintenance
```bash
# Check embedding database health
python src/embedding/diagnose_db.py

# Check for duplicate chunk IDs
python src/embedding/check_duplicate_ids.py

# Delete specific chunks by table type
python scripts/delete_table_chunks.py

# Test Google Cloud AI Platform integration
python diag.py
```

## Architecture

### Data Flow
1. **Raw Data Sources** (`data/raw_sdk_docs/`):
   - `api_docs_html/V2.00.00/` - HTML API documentation
   - `docs/V1.14.00/`, `docs/V2.00.00/` - PDF documentation
   - `sdk_source/` - C++ header files
   - `doxygen_examples_xml_output/` - Doxygen-generated examples

2. **Parsing Layer** (`src/parsing/`):
   - Multi-format parsers extract structured content
   - Version-aware processing (V1.14.00, V2.00.00)
   - Content stored in `data/parsed_data/` by format and version

3. **Chunking System** (`src/parsing/chunker.py`):
   - Sliding window chunking (500 chars, 100 overlap)
   - Boilerplate removal and content cleaning
   - Unique chunk ID generation
   - Output: `data/chunks.json`

4. **Embedding System** (`src/embedding/`):
   - Local embeddings using SentenceTransformer (`multi-qa-mpnet-base-dot-v1`)
   - ChromaDB vector storage (`data/chroma_db/`)
   - Metadata filtering by content type
   - Batch processing for efficiency

5. **RAG Query System** (`src/rag/query_system.py`):
   - Query classification (API search, examples, compatibility)
   - Semantic similarity search
   - Context-aware response generation using Ollama (codellama:13b model)

### Key Components

#### Parsing System
- **Multi-format support**: HTML, PDF, XML, C++, Markdown, RST
- **Version handling**: Separate processing for SDK versions
- **Content extraction**: Text, tables, code examples, API documentation
- **Doxygen integration**: Automated C++ header parsing

#### Embedding & Retrieval  
- **Local embeddings**: Uses `multi-qa-mpnet-base-dot-v1` model for offline processing
- **ChromaDB**: Vector database with metadata filtering
- **Content types**: `summary`, `member`, `example_code`, `documentation_text`, `documentation_table`
- **Chunking strategy**: Configurable size and overlap parameters

#### Query Processing
- **Query classification**: Automatic detection of query intent
- **Document filtering**: Type-based retrieval optimization  
- **Response generation**: Integration with local Ollama models
- **Debug mode**: Detailed logging for troubleshooting

## Configuration

### Key Configuration Constants
- `CHUNK_SIZE = 500` - Size of text chunks for embedding
- `CHUNK_OVERLAP = 100` - Overlap between chunks
- `COLLECTION_NAME = "sdk_docs_local"` - ChromaDB collection
- `MODEL_NAME = 'multi-qa-mpnet-base-dot-v1'` - Embedding model
- `OLLAMA_MODEL = "codellama:13b"` - Response generation model

### Test Mode Configuration
Most scripts include test mode flags for development:
- `TEST_MODE = True` - Process limited data for testing
- `TEST_CHUNK_LIMIT` - Number of chunks to process in test mode
- `METADATA_TYPE_FILTER` - Filter embeddings by content type

## Directory Structure

```
├── data/                           # All data storage
│   ├── raw_sdk_docs/              # Original SDK documentation
│   │   ├── api_docs_html/         # HTML API docs by version
│   │   ├── docs/                  # PDF documentation by version
│   │   └── sdk_source/            # C++ source code
│   ├── parsed_data/               # Structured extracted data
│   │   ├── cpp/, html/, pdf/      # By format and version
│   │   └── markdown/, rst/, text/
│   ├── chroma_db/                 # Vector database
│   └── chunks.json                # Final chunked content
├── src/                           # Source code
│   ├── parsing/                   # Document parsing modules
│   ├── embedding/                 # Embedding and storage
│   └── rag/                      # Query and retrieval system
└── scripts/                       # Utility scripts
```

## Development Notes

### Dependencies
This project uses SentenceTransformer, ChromaDB, LangChain, pdfplumber, BeautifulSoup4, and Ollama for local LLM processing.

### Version Management
The system handles multiple SDK versions (V1.14.00, V2.00.00) with version-specific parsing and storage paths.

### Performance Considerations
- Batch processing in embedding generation
- ChromaDB for efficient similarity search
- Local models for offline operation
- Configurable chunk sizes for memory management

## ✅ **COMPLETED: MCP Server Implementation & Railway Deployment** (Sept 5, 2025)

### **🎉 SUCCESS: Claude Web Can Now Access Our RAG System!**

After multiple failed attempts with custom implementations, I successfully created a proper MCP server using the official FastMCP SDK patterns. **Claude Web UI can now connect to our server and access the RAG system.**

### **What Finally Worked: Official FastMCP Implementation**

#### **Key Implementation (`mcp_server_simple.py`):**
```python
from mcp.server.fastmcp import FastMCP
import contextlib
from starlette.applications import Starlette
from starlette.routing import Mount, Route

# Create FastMCP server with stateless HTTP - CRITICAL for web deployment
mcp = FastMCP("SDK RAG Server", stateless_http=True)

# Proper lifespan management - handles RAG initialization and session management
@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    global rag_search
    async with contextlib.AsyncExitStack() as stack:
        # Initialize RAG search system
        rag_search = RAGSearch()
        # Start MCP session manager - CRITICAL
        await stack.enter_async_context(mcp.session_manager.run())
        yield

# Clean Starlette mounting pattern from official examples
app = Starlette(
    routes=[
        Route("/health", health_check),
        Mount("/", mcp.streamable_http_app()),  # MCP at root - KEY INSIGHT
    ],
    lifespan=lifespan,
)
```

#### **6 MCP Tools Successfully Registered:**
```python
@mcp.tool()
def search_sdk(query: str, top_k: int = 5) -> str:
    """Search the Camera Remote SDK documentation and code examples."""

@mcp.tool()  
def search_code_examples(query: str, top_k: int = 5) -> str:
    """Search specifically for C++ code examples and implementations."""

@mcp.tool()
def search_documentation(query: str, top_k: int = 5) -> str:
    """Search SDK documentation text (guides, tutorials, explanations)."""

@mcp.tool()
def search_api_functions(query: str, top_k: int = 5) -> str:
    """Search API function definitions and signatures."""

@mcp.tool()
def search_compatibility(query: str, top_k: int = 5) -> str:
    """Search camera compatibility tables and structured data."""

@mcp.tool()
def get_sdk_stats() -> str:
    """Get statistics about the SDK documentation database."""
```

### **Critical Success Factors:**

#### **1. Used Official FastMCP SDK Patterns**
- ❌ **Previous failures**: Custom FastAPI/SSE implementations
- ✅ **What worked**: Official `mcp.server.fastmcp.FastMCP` with `stateless_http=True`
- ✅ **Key insight**: Follow `/tmp/python-sdk/examples/streamable_starlette_mount.py` exactly

#### **2. Proper Session Management**  
- ✅ **Lifespan management**: `@contextlib.asynccontextmanager` for initialization
- ✅ **Session manager**: `await stack.enter_async_context(mcp.session_manager.run())`
- ✅ **RAG initialization**: Global `rag_search` properly initialized in lifespan

#### **3. Correct Railway Deployment Configuration**
```toml
# railway.toml - Updated to use proper server
[deploy]
startCommand = "python3 mcp_server_simple.py"  # Changed from mcp_server.py
healthcheckPath = "/health"
```

#### **4. Clean URL Structure**
- ✅ **Health endpoint**: `https://sdk-rag-agent-production.up.railway.app/health`
- ✅ **MCP endpoint**: `https://sdk-rag-agent-production.up.railway.app/mcp` 
- ✅ **SSE transport**: Correctly requires `Accept: text/event-stream` header

### **Deployment Success Verification:**

#### **Health Check Working:**
```bash
$ curl https://sdk-rag-agent-production.up.railway.app/health
{"status":"healthy","service":"fastmcp-server","rag_initialized":true,"mcp_path":"/mcp"}
```

#### **MCP Endpoint Working:**
```bash
$ curl -H "Accept: text/event-stream" https://sdk-rag-agent-production.up.railway.app/mcp
# Returns SSE stream (correctly establishes persistent connection)
```

#### **Claude Web Connection:**
- ✅ **URL**: `https://sdk-rag-agent-production.up.railway.app`
- ✅ **Tools detected**: All 6 MCP tools available
- ✅ **RAG queries working**: Can search SDK documentation via Claude Web UI

### **What Didn't Work (For Future Reference):**

#### **❌ Failed Approach 1: Custom FastAPI Implementation**
```python
# This approach failed - don't repeat
app = FastAPI()
@app.get("/sse")  
async def custom_sse():
    # Custom SSE implementation - wrong approach
```

#### **❌ Failed Approach 2: Complex ASGI Mounting**
```python
# This approach failed - over-complicated
class MCPWithHealth:
    def __init__(self, mcp_app):
        # Custom ASGI wrapper - unnecessary complexity
```

#### **❌ Failed Approach 3: Wrong SDK Usage**
```python
# This approach failed - wrong SDK pattern
from mcp.server import Server  # Wrong import
server = Server("sdk-rag-server")  # Wrong initialization
```

### **Final Architecture (Working):**
```
Claude Web UI → HTTPS → Railway → FastMCP Server → Pinecone RAG (8,962 vectors)
                           ↓
                    6 MCP Tools Available:
                    - search_sdk
                    - search_code_examples  
                    - search_documentation
                    - search_api_functions
                    - search_compatibility
                    - get_sdk_stats
```

### **Key Lessons Learned:**
1. **Always use official SDK patterns** - custom implementations waste time
2. **Follow examples exactly** - `/tmp/python-sdk/examples/` are the source of truth
3. **FastMCP with stateless_http=True** - essential for web deployment
4. **Session manager is critical** - handles MCP protocol properly
5. **Mount at root path** - MCP clients expect clean URL structure

The MCP server is now **production-ready** and **working with Claude Web UI**! 🎉

## TODO: C++ Source Code Chunking Improvements

### Current Status (as of Sept 2, 2025)
- ✅ **Initial C++ chunker implemented** (`src/parsing/cpp_source_chunker.py`)
- ✅ **231 chunks extracted** from 5 C++ source files
- ✅ **Multi-model embedding system** (CodeBERT for code, all-mpnet-base-v2 for docs)
- ❌ **Issues identified** requiring fixes tomorrow

### Issues to Fix Tomorrow:

#### 1. Remove Context Bloat (High Priority)
**Problem**: Every chunk starts with 20+ unnecessary includes (~1000 chars of noise)
```cpp
// Current (bad):
#include <SDKDDKVer.h>
#include <windows.h>
... 20+ includes ...
bool CameraDevice::connect(...) { ... }

// Target (good):
bool CameraDevice::connect(SCRSDK::CrSdkControlMode openMode, SCRSDK::CrReconnectingSet reconnect)
{
    // Pure function implementation only
}
```

**Solution**: Remove `extract_includes_and_namespaces()` entirely - store only pure function code.

#### 2. Capture Missing Code (Critical)
**Current Coverage Issues**:
- ✅ CameraDevice.cpp: 96.3% coverage (good)
- ❌ CrDebugString.cpp: 0.6% coverage (terrible - missing ~1400 lines)
- ❌ ConnectionInfo.cpp: 54.5% coverage (missing functions)

**Missing Code Types**:
```python
# Static data maps (0% captured, very valuable for SDK):
const std::unordered_map<CrInt32, std::string> map_CrCommandId { ... };
const std::unordered_map<CrInt32, std::string> map_CrDeviceProperty { ... };

# Standalone functions (missed):
std::string CrCommandIdString(SCRSDK::CrCommandId id);
std::string CrErrorString(SCRSDK::CrError error);
CrInt32 getMapCode(const std::unordered_map<CrInt32, std::string>* _map, std::string name);
```

### Implementation Plan for Tomorrow:

#### Step 1: Clean Function Extraction
```python
# DELETE: extract_includes_and_namespaces() function
# CHANGE: Store only pure function implementation
# RESULT: ~50% smaller chunks, better semantic focus for CodeBERT
```

#### Step 2: Add Missing Patterns
```python
# Add patterns for:
static_map_pattern = r'^const\s+std::unordered_map<[^>]+>\s+([a-zA-Z_]\w*)\s*{'
standalone_functions = [
    r'^std::string\s+([a-zA-Z_]\w*)\s*\(',
    r'^CrInt32\s+([a-zA-Z_]\w*)\s*\(',
    r'^static\s+std::string\s+([a-zA-Z_]\w*)\s*\('
]
```

#### Step 3: Verification
- Target 95%+ coverage for all .cpp files
- Estimated result: ~300-350 total chunks (up from 231)
- Quality check: No include bloat, only relevant function code

### Expected Benefits:
1. **Better RAG retrieval** - CodeBERT focuses on actual code logic, not includes
2. **Complete SDK coverage** - All utility functions and enum mappings captured  
3. **Smaller, cleaner chunks** - Better for browser context limits
4. **Cursor-IDE quality** - Complete function implementations for code generation

### Files to Update:
- ✅ `src/parsing/cpp_source_chunker.py` - Fixed patterns and removed context bloat
- ✅ Re-run embedding with improved chunks
- ✅ Update documentation after completion

## ✅ **COMPLETED: C++ Source Code Chunking & Cloud RAG System** (Sept 3, 2025)

### C++ Chunking Results:
- ✅ **Fixed context bloat** - Removed includes/namespaces from chunks (~50% size reduction)
- ✅ **Improved function detection** - Better patterns for static functions and SCRSDK types  
- ✅ **Added static map extraction** - Captured 15 valuable SDK enum/error maps
- ✅ **Eliminated false positives** - Fixed RemoteCli.cpp indented function calls issue
- ✅ **Final results**: 229 clean, accurate chunks from 5 C++ files
  - CameraDevice.cpp: 97.1% coverage (201/207 functions)
  - CrDebugString.cpp: 104.2% coverage (25/24 - includes maps)
  - RemoteCli.cpp: 100.0% coverage (1/1 function)

### Cloud Migration & MCP Server:
- ✅ **ChromaDB → Pinecone migration** - All 8,962 embeddings successfully migrated
- ✅ **Smart chunk splitting** - Handled 40KB metadata limit by splitting large chunks
- ✅ **FastAPI MCP Server** built in `/mcp/` folder:
  - `server.py` - Main MCP server with all endpoints  
  - `search.py` - Pinecone search with content type filtering
  - `requirements.txt` - Dependencies for cloud deployment
  - `railway.toml` - Railway deployment configuration
  - `test_server.py` - Local testing script
  - `README.md` - Complete documentation

### Content Type Distribution (8,962 total chunks):
- **documentation_table**: 5,230 chunks (camera compatibility tables)
- **documentation_text**: 2,220 chunks (guides, tutorials)
- **enum**: 528 chunks (enumeration definitions)
- **function**: 353 chunks (API function definitions) 
- **variable**: 322 chunks (variable definitions)
- **example_code**: 229 chunks (C++ code implementations)
- **summary**: 56 chunks (API summaries)
- **typedef**: 17 chunks (type definitions)
- **define**: 7 chunks (preprocessor defines)

### MCP Endpoints Ready:
- `GET /search` - General search across all content
- `GET /search/code` - C++ code examples (229 chunks)
- `GET /search/docs` - Documentation text (2,220 chunks)
- `GET /search/compatibility` - Camera compatibility tables (5,230 chunks)
- `GET /search/functions` - API functions (353 chunks)
- `GET /health` - System health check
- `GET /stats` - Database statistics
- `GET /mcp/tools` - MCP tool definitions

### Next Steps:
1. **Deploy to Railway** - Push `/mcp` folder to Railway with Pinecone API key
2. **Test locally first** - Run `python mcp/server.py` and `python mcp/test_server.py`
3. **Connect to ChatGPT/Claude** - Use Railway URL for MCP integration
4. **Test end-to-end** - Verify SDK queries work through AI assistants

### System Architecture:
```
ChatGPT/Claude ↔️ MCP Server (Railway) ↔️ Pinecone (8,962 vectors) 
                        ↕️
                 SentenceTransformer (Query Embeddings)
```

The Camera Remote SDK RAG system is now **cloud-ready** with comprehensive content type support and MCP protocol integration!