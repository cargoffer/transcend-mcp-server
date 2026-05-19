"""
Servidor MCP de TRANSCEND.

Punto de entrada que configura e inicia el servidor FastMCP
con todas las herramientas registradas.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from transcend_mcp.client import TranscendClient
from transcend_mcp.config import settings
from transcend_mcp.tools import register_tools

logger = logging.getLogger(__name__)

# Nombre del servidor tal como se anuncia en el protocolo MCP
SERVER_NAME = "transcend-mcp"


def _configure_logging() -> None:
    """Configura el logging con formato limpio y nivel desde settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def _module_urls_summary() -> str:
    """Resumen de URLs de los módulos configurados."""
    env = settings.env
    from transcend_mcp.config import MODULE_SERVERS

    servers = MODULE_SERVERS.get(env, MODULE_SERVERS["production"])
    lines = [f"  Entorno: {env}"]
    for mod, url in servers.items():
        lines.append(f"    {mod:<10s} → {url}")
    return "\n".join(lines)


def _print_banner() -> None:
    """Muestra un banner informativo al arrancar el servidor."""
    banner = f"""
╔══════════════════════════════════════════════════════════╗
║                  TRANSCEND MCP Server                   ║
║  Logística y transporte inteligente                     ║
╠══════════════════════════════════════════════════════════╣
║  API Key  : {"✓ configurada" if settings.transcend_api_key else "✗ NO CONFIGURADA":<39s}║
║  Log Level: {settings.log_level:<39s}║
╠══════════════════════════════════════════════════════════╣
{_module_urls_summary()}
╚══════════════════════════════════════════════════════════╝
"""
    logger.info("\n%s", banner)


def create_server() -> tuple[FastMCP, TranscendClient]:
    """
    Crea y configura el servidor MCP con todas las herramientas.

    Returns:
        Tupla (mcp_server, api_client) para que el llamador
        pueda gestionar el ciclo de vida.
    """
    _configure_logging()
    _print_banner()

    mcp = FastMCP(
        name=SERVER_NAME,
        instructions=(
            "TRANSCEND Logistics MCP Server — "
            "Calcula rutas optimizadas para camiones, costos de transporte, "
            "peajes, condiciones meteorológicas, puntos de interés "
            "(aparcamientos, gasolineras, talleres, duchas), "
            "puntos negros de tráfico y estaciones de servicio. "
            "Usa datos reales de los microservicios de TRANSCEND."
        ),
    )

    client = TranscendClient()

    register_tools(mcp, client)

    logger.info("Herramientas MCP registradas correctamente.")
    return mcp, client


def main() -> None:
    """
    Punto de entrada principal.

    Arranca el servidor MCP. Por defecto usa transporte stdio
    (el estándar MCP). Si se configura MCP_HOST != 127.0.0.1
    arranca en modo HTTP/sse.
    """
    mcp, client = create_server()

    # El propio FastMCP gestiona el transporte según el contexto:
    #   - Por defecto: stdio (estándar MCP para Claude Desktop, etc.)
    #   - Con run(transport="sse"): HTTP SSE
    transport = "sse" if settings.mcp_host != "127.0.0.1" else "stdio"

    try:
        logger.info("Iniciando servidor MCP (transporte: %s)...", transport)
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario.")
    finally:
        import asyncio

        asyncio.run(client.close())
        logger.info("Cliente HTTP cerrado. ¡Hasta luego!")


if __name__ == "__main__":
    main()
