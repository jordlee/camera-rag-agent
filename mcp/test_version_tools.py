#!/usr/bin/env python3
"""Test script for version management MCP tools."""

import sys
import json
sys.path.append('..')

from search import RAGSearch

# Initialize RAG search
print("Initializing RAG search...")
rag_search = RAGSearch()
print()

# Simulate MCP tool calls
print("=== Testing MCP Tool: get_current_sdk_version ===")
version_info = rag_search.list_versions()
response = {
    "current_version": rag_search.get_version(),
    "available_versions": version_info["available"],
    "help": "Use set_sdk_version() to switch versions"
}
print(json.dumps(response, indent=2))
print()

print("=== Testing MCP Tool: set_sdk_version('V1.14.00') ===")
result = rag_search.set_version("V1.14.00")
version_info = rag_search.list_versions()
response = {
    "message": result,
    "active_version": rag_search.get_version(),
    "available_versions": version_info["available"],
    "note": "All search tools will now use this version until changed again."
}
print(json.dumps(response, indent=2))
print()

print("=== Testing Search After Version Change ===")
results = rag_search.search("camera connect", top_k=1)
print(f"Search results from {rag_search.get_version()}:")
print(json.dumps(results[0], indent=2))
print()

print("=== Testing MCP Tool: set_sdk_version('V2.00.00') ===")
result = rag_search.set_version("V2.00.00")
version_info = rag_search.list_versions()
response = {
    "message": result,
    "active_version": rag_search.get_version(),
    "available_versions": version_info["available"],
    "note": "All search tools will now use this version until changed again."
}
print(json.dumps(response, indent=2))
print()

print("=== Testing Search After Version Change ===")
results = rag_search.search("camera connect", top_k=1)
print(f"Search results from {rag_search.get_version()}:")
print(json.dumps(results[0], indent=2))
print()

print("✅ All MCP tool tests passed!")
