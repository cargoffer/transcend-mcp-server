"""
Punto de entrada principal del servidor MCP de TRANSCEND.

Arranca el servidor FastMCP y lo pone a disposición de clientes
compatibles con el Model Context Protocol (MCP).

Uso:
    python -m transcend_mcp

O desde un cliente MCP compatible (Claude Desktop, etc.):
    {
        "mcpServers": {
            "transcend": {
                "command": "python",
                "args": ["-m", "transcend_mcp"],
                "env": {
                    "TRANSCEND_API_KEY": "tu-api-key",
                    "TRANSCEND_ENV": "production"
                }
            }
        }
    }
"""

from transcend_mcp.server import main

if __name__ == "__main__":
    main()
