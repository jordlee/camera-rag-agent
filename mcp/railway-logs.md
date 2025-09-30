{"message":"INFO:     100.64.0.6:40982 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-30T16:52:49.100892381Z"}
{"message":"2025-09-30 16:52:45,547 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:49.100897126Z"}
{"message":"\rBatches:   0%|          | 0/1 [00:00<?, ?it/s]\rBatches: 100%|██████████| 1/1 [00:04<00:00,  4.23s/it]\rBatches: 100%|██████████| 1/1 [00:04<00:00,  4.23s/it]","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:49.783967258Z"}
{"message":"2025-09-30 16:52:49,777 - search - WARNING - Embedding took 4.23s (exceeds 3.0s limit)","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:49.783981421Z"}
{"message":"2025-09-30 16:52:50,156 - search - INFO - Found 10 results for query: remote transfer mode requirements settings configu...","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173812894Z"}
{"message":"2025-09-30 16:52:50,159 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173821314Z"}
{"message":"INFO:     100.64.0.9:15724 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-30T16:52:50.173826070Z"}
{"message":"2025-09-30 16:52:50,163 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173830986Z"}
{"message":"2025-09-30 16:52:50,164 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173836924Z"}
{"message":"2025-09-30 16:52:50,164 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173842941Z"}
{"message":"2025-09-30 16:52:50,165 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.173848911Z"}
{"message":"INFO:     100.64.0.8:52918 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-30T16:52:50.329016572Z"}
{"message":"2025-09-30 16:52:50,325 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.329216542Z"}
{"message":"INFO:     100.64.0.3:30480 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-30T16:52:50.537707744Z"}
{"message":"2025-09-30 16:52:50,525 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:52:50.537714260Z"}
{"message":"INFO:     100.64.0.5:24522 - \"HEAD /mcp HTTP/1.1\" 405 Method Not Allowed","attributes":{"level":"info"},"timestamp":"2025-09-30T16:55:00.570649941Z"}
{"message":"2025-09-30 16:54:56,867 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570659223Z"}
{"message":"2025-09-30 16:54:56,867 - mcp.server.streamable_http - ERROR - Error in message router","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570665801Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570672139Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/mcp/server/streamable_http.py\", line 831, in message_router","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570678128Z"}
{"message":"    async for session_message in write_stream_reader:","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570687758Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/abc/_streams.py\", line 41, in __anext__","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570694128Z"}
{"message":"    return await self.receive()","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570700221Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570706056Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 111, in receive","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570711842Z"}
{"message":"    return self.receive_nowait()","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570717490Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570724103Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 93, in receive_nowait","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570730281Z"}
{"message":"    raise ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570735988Z"}
{"message":"anyio.ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-30T16:55:00.570745297Z"}
{"message":"INFO:     100.64.0.5:24522 - \"GET /.well-known/oauth-protected-resource/mcp HTTP/1.1\" 404 Not Found","attributes":{"level":"info"},"timestamp":"2025-09-30T16:55:00.570751148Z"}