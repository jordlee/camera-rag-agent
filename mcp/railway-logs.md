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


5
RUN pip install --no-cache-dir -r requirements.txt
3s
Looking in indexes: https://pypi.org/simple, https://download.pytorch.org/whl/cpu
Collecting fastapi==0.116.1 (from -r requirements.txt (line 2))
  Downloading fastapi-0.116.1-py3-none-any.whl.metadata (28 kB)
Collecting uvicorn==0.35.0 (from uvicorn[standard]==0.35.0->-r requirements.txt (line 3))
  Downloading uvicorn-0.35.0-py3-none-any.whl.metadata (6.5 kB)
Collecting hypercorn==0.17.3 (from -r requirements.txt (line 4))
  Downloading hypercorn-0.17.3-py3-none-any.whl.metadata (5.4 kB)
Collecting python-dotenv==1.1.1 (from -r requirements.txt (line 5))
  Downloading python_dotenv-1.1.1-py3-none-any.whl.metadata (24 kB)
Collecting pydantic==2.11.7 (from -r requirements.txt (line 6))
  Downloading pydantic-2.11.7-py3-none-any.whl.metadata (67 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 68.0/68.0 kB 13.2 MB/s eta 0:00:00
Collecting httpx==0.28.1 (from -r requirements.txt (line 7))
  Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting starlette (from -r requirements.txt (line 8))
  Downloading starlette-0.47.3-py3-none-any.whl.metadata (6.2 kB)
ERROR: Could not find a version that satisfies the requirement psutil==6.1.2 (from versions: 0.1.1, 0.1.2, 0.1.3, 0.2.0, 0.2.1, 0.3.0, 0.4.0, 0.4.1, 0.5.0, 0.5.1, 0.6.0, 0.6.1, 0.7.0, 0.7.1, 1.0.0, 1.0.1, 1.1.0, 1.1.1, 1.1.2, 1.1.3, 1.2.0, 1.2.1, 2.0.0, 2.1.0, 2.1.1, 2.1.2, 2.1.3, 2.2.0, 2.2.1, 3.0.0, 3.0.1, 3.1.0, 3.1.1, 3.2.0, 3.2.1, 3.2.2, 3.3.0, 3.4.1, 3.4.2, 4.0.0, 4.1.0, 4.2.0, 4.3.0, 4.3.1, 4.4.0, 4.4.1, 4.4.2, 5.0.0, 5.0.1, 5.1.0, 5.1.1, 5.1.2, 5.1.3, 5.2.0, 5.2.1, 5.2.2, 5.3.0, 5.3.1, 5.4.0, 5.4.1, 5.4.2, 5.4.3, 5.4.4, 5.4.5, 5.4.6, 5.4.7, 5.4.8, 5.5.0, 5.5.1, 5.6.0, 5.6.1, 5.6.2, 5.6.3, 5.6.4, 5.6.5, 5.6.6, 5.6.7, 5.7.0, 5.7.1, 5.7.2, 5.7.3, 5.8.0, 5.9.0, 5.9.1, 5.9.2, 5.9.3, 5.9.4, 5.9.5, 5.9.6, 5.9.7, 5.9.8, 6.0.0, 6.1.0, 6.1.1, 7.0.0)
ERROR: No matching distribution found for psutil==6.1.2
[notice] A new release of pip is available: 24.0 -> 25.2
[notice] To update, run: pip install --upgrade pip
Dockerfile:16
-------------------
14 |
15 |     # Install Python dependencies with CPU-only PyTorch
16 | >>> RUN pip install --no-cache-dir -r requirements.txt
17 |
18 |     # Copy application code
-------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
