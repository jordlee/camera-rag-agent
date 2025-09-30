# Known Issues to Investigate

## 1. ClosedResourceError During MCP Handshake (Discovered: Sept 30, 2025)

### Symptom
`anyio.ClosedResourceError` occurs during MCP protocol handshake, even before tool invocation:

```
2025-09-30 10:41:45,953 - mcp.server.streamable_http - INFO - Terminating session: None
2025-09-30 10:41:45,953 - mcp.server.streamable_http - ERROR - Error in message router
Traceback (most recent call last):
  File ".../mcp/server/streamable_http.py", line 831, in message_router
    async for session_message in write_stream_reader:
  File ".../anyio/streams/memory.py", line 93, in receive_nowait
    raise ClosedResourceError
anyio.ClosedResourceError
```

### Context
- Occurs when testing MCP endpoint with curl/HTTP clients
- Happens during `ListToolsRequest` processing
- Server is using `stateless_http=True` mode in FastMCP
- Error is at the FastMCP SDK level, not our application code

### Difference from Fixed Issue
This is **separate** from the timeout issue we just fixed:
- **Fixed issue**: Slow `search_with_intent()` (4.23s) causing timeout during tool execution
- **This issue**: Session terminating prematurely during MCP protocol handshake

### Impact
- May affect Claude Web connections during initial tool discovery
- Doesn't prevent successful tool calls (session recreates)
- Happens more frequently with rapid consecutive requests

### Possible Root Causes
1. **FastMCP session lifecycle**: `stateless_http=True` may be too aggressive with session cleanup
2. **Client expectations**: MCP clients might not handle stateless sessions correctly
3. **Race condition**: Write stream closes before read completes

### Investigation Steps
1. Test with official MCP client (not curl)
2. Try `stateless_http=False` mode (requires persistent connections)
3. Review FastMCP SDK source: `/mcp/server/streamable_http.py:831`
4. Check if issue occurs on Railway with Claude Web (real-world test)
5. Monitor Railway logs after timeout fix deployment

### Workarounds
- None needed currently - doesn't block functionality
- May need to implement connection pooling if issue persists

### Priority
**Medium** - Monitor after deploying timeout fix. If Railway logs show this frequently with Claude Web, escalate to High.

---

## Related Files
- `mcp/mcp_server.py` - Main server implementation
- `mcp/railway-logs.md` - Production error logs
