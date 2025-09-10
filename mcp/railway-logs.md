{"message":"INFO:     100.64.0.3:20370 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:19:30.312256669Z"}
{"message":"2025-09-10 17:19:29,128 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312266076Z"}
{"message":"INFO:     100.64.0.4:42726 - \"POST /mcp HTTP/1.1\" 202 Accepted","attributes":{"level":"info"},"timestamp":"2025-09-10T17:19:30.312272595Z"}
{"message":"2025-09-10 17:19:29,676 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312278603Z"}
{"message":"INFO:     100.64.0.3:20370 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:19:30.312283803Z"}
{"message":"2025-09-10 17:19:29,819 - mcp.server.lowlevel.server - INFO - Processing request of type ListResourcesRequest","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312315063Z"}
{"message":"2025-09-10 17:19:29,820 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312321707Z"}
{"message":"INFO:     100.64.0.5:42072 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:19:30.312327718Z"}
{"message":"INFO:     100.64.0.5:42082 - \"POST /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:19:30.312334954Z"}
{"message":"2025-09-10 17:19:29,935 - mcp.server.lowlevel.server - INFO - Processing request of type ListPromptsRequest","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312341277Z"}
{"message":"2025-09-10 17:19:29,935 - mcp.server.lowlevel.server - INFO - Processing request of type ListToolsRequest","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312348167Z"}
{"message":"2025-09-10 17:19:29,936 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312354444Z"}
{"message":"2025-09-10 17:19:29,936 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:19:30.312361227Z"}
{"message":"INFO:     100.64.0.6:46172 - \"GET /mcp HTTP/1.1\" 200 OK","attributes":{"level":"info"},"timestamp":"2025-09-10T17:20:30.333619805Z"}
{"message":"INFO:     100.64.0.6:58026 - \"HEAD /mcp HTTP/1.1\" 405 Method Not Allowed","attributes":{"level":"info"},"timestamp":"2025-09-10T17:20:50.334174070Z"}
{"message":"2025-09-10 17:20:47,137 - mcp.server.streamable_http - INFO - Terminating session: None","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334182201Z"}
{"message":"2025-09-10 17:20:47,137 - mcp.server.streamable_http - ERROR - Error in message router","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334188073Z"}
{"message":"Traceback (most recent call last):","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334193399Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/mcp/server/streamable_http.py\", line 831, in message_router","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334199033Z"}
{"message":"    async for session_message in write_stream_reader:","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334204202Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/abc/_streams.py\", line 41, in __anext__","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334212156Z"}
{"message":"    return await self.receive()","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334217749Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334223522Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 111, in receive","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334229128Z"}
{"message":"    return self.receive_nowait()","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334234644Z"}
{"message":"           ^^^^^^^^^^^^^^^^^^^^^","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334239811Z"}
{"message":"  File \"/usr/local/lib/python3.11/site-packages/anyio/streams/memory.py\", line 93, in receive_nowait","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334245424Z"}
{"message":"    raise ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334251436Z"}
{"message":"anyio.ClosedResourceError","attributes":{"level":"error"},"timestamp":"2025-09-10T17:20:50.334257281Z"}