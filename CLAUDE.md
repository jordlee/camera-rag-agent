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

## TODO: Create Proper MCP Server (Sept 5, 2025)

### Current Status
- ✅ Created FastAPI REST API with MCP-like endpoints
- ✅ Successfully deployed to Railway
- ✅ Working search endpoints accessible via HTTP
- ❌ Not a true MCP server - LM Studio and Claude can't connect
- ❌ FastAPI returns wrong content-type for SSE (application/json instead of text/event-stream)

### The Problem
We built a REST API with MCP-style endpoints, but MCP clients (LM Studio, Claude Desktop) expect:
1. **True MCP protocol** - JSON-RPC 2.0 over stdio or SSE transport
2. **Official MCP SDK** - Not custom FastAPI implementation
3. **Proper message handling** - Bidirectional communication, session management

### Tomorrow's Plan: Build Proper MCP Server

#### Step 1: Install Official MCP SDK
```bash
pip install mcp
```

#### Step 2: Create New MCP Server
Create `mcp_server.py` using official SDK:
```python
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializeResult
import mcp.server.stdio
import mcp.types as types

# Initialize with our existing RAG search
from search import RAGSearch

server = Server("sdk-rag-server")
rag_search = RAGSearch()

@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="search_sdk",
            description="Search SDK documentation",
            inputSchema={...}
        ),
        # Add other tools
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "search_sdk":
        return rag_search.search(...)
    # Handle other tools

# Run with stdio transport
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializeResult(
                protocol_version="2025-03-26",
                capabilities=server.get_capabilities()
            )
        )
```

#### Step 3: Test Locally
```bash
# Test with MCP client
python mcp_server.py

# Configure in Claude/LM Studio with command:
# python /path/to/mcp_server.py
```

#### Step 4: Deploy Options
1. **For Claude Desktop**: Run locally with stdio transport
2. **For web access**: Deploy with SSE transport to Railway
3. **Keep REST API**: Maintain current FastAPI for web dashboard

### Files to Keep
- `search.py` - RAG search logic (works great!)
- `server.py` - Keep as REST API for web access
- All parsing/embedding code - Already complete

### Benefits of Proper MCP Server
1. **Native compatibility** - Works with all MCP clients
2. **Proper protocol** - Handles JSON-RPC correctly
3. **Official support** - Uses Anthropic's SDK
4. **Simpler code** - No manual SSE/protocol implementation

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