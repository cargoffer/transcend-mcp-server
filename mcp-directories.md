# TRANSCEND MCP Server — Directory Submissions

This file tracks where the TRANSCEND MCP Server has been submitted for discovery.

## Directories

### 1. Smithery.ai
- URL: https://smithery.ai
- Status: ✅ Submitted
- Entry: "transcend-mcp-server"
- Config: Python ≥ 3.10, requires TRANSCEND_API_KEY env var

### 2. MCP.so
- URL: https://mcp.so
- Status: ✅ Submitted
- Entry: "transcend-mcp"

### 3. Glama.ai
- URL: https://glama.ai/mcp/servers
- Status: ⏳ Pending

### 4. PulseMCP
- URL: https://pulsemcp.com
- Status: ⏳ Pending

### 5. MCPGet
- URL: https://mcpget.com
- Status: ⏳ Pending

## Submission commands

### Smithery CLI (if installed)
```bash
npx @smithery/cli submit
```

### Manual submission
Each directory has a submission form. Required info:
- Repository: https://github.com/cargoffer/transcend-mcp-server
- Package: transcend-mcp (PyPI)
- Python version: ≥ 3.10
- Environment variables: TRANSCEND_API_KEY
- Transport: stdio (default), HTTP/SSE (MCP_PORT=8100)
