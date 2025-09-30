To setup your MCP server in Claude Code, find your .claude.json file and navigate to the local project configuration that you want to use claude code in. Add the following configuration lines:

"mcpContextUris": [],
      "mcpServers": {
        "crsdk": {
          "command": "npx",
          "args": [
            "mcp-remote",
            "https://sdk-rag-agent-production.up.railway.app/mcp"
          ]
        }
      },
      