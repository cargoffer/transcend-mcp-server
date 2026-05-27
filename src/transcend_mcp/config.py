"""
Configuración del servidor MCP de TRANSCEND.

Usa dos entornos seleccionables mediante TRANSCEND_ENV:
  - "production" (default): apunta a los servidores de producción reales
  - "release-dev": apunta a los servidores de release/pre-lanzamiento

Cada módulo de TRANSCEND corre en su propio servidor, por lo que
definimos aquí un mapa de módulo → URL base para cada entorno.
"""

import logging
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings

# ── Entornos ─────────────────────────────────────────────────────────────

EnvName = Literal["production", "release-dev"]

MODULE_SERVERS: dict[EnvName, dict[str, str]] = {
    "production": {
        "tolls": "https://back.transcend.cargoffer.com/transcend/tolls",
        "poi": "https://back.transcend.cargoffer.com/transcend/poi",
        "stations": "https://back.transcend.cargoffer.com/transcend/stations",
        "weather": "https://back.transcend.cargoffer.com/transcend/weather",
        "traffic": "https://back.transcend.cargoffer.com/transcend/traffic",
    },
    "release-dev": {
        "tolls": "https://back.transcend.cargoffer.com/transcend/tolls",
        "poi": "https://back.transcend.cargoffer.com/transcend/poi",
        "stations": "https://back.transcend.cargoffer.com/transcend/stations",
        "weather": "https://back.transcend.cargoffer.com/transcend/weather",
        "traffic": "https://back.transcend.cargoffer.com/transcend/traffic",
    },
}


class Settings(BaseSettings):
    """
    Configuración del servidor MCP de TRANSCEND.

    Las variables se leen desde el entorno o un archivo .env en
    el directorio de trabajo o en ~/.transcend/.env
    """

    # --- TRANSCEND API ---
    transcend_api_key: str = ""
    transcend_env: str = "production"

    # --- MCP Server ---
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8100

    # --- Logging ---
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def env(self) -> EnvName:
        """Entorno activo (normalizado)."""
        val = self.transcend_env.lower().replace("-", "_")
        if val in ("release", "release_dev", "release-dev"):
            return "release-dev"
        return "production"

    def module_url(self, module: str) -> str:
        """Devuelve la URL base para el módulo indicado según el entorno activo."""
        servers = MODULE_SERVERS.get(self.env, MODULE_SERVERS["production"])
        return servers.get(module, "")


def load_settings() -> Settings:
    """
    Carga la configuración buscando .env en varias ubicaciones.

    Orden de precedencia (mayor a menor):
    1. Variables de entorno del sistema
    2. .env en el directorio de trabajo actual
    3. ~/.transcend/.env
    4. Valores por defecto en Settings
    """
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".transcend" / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            logging.debug("Cargando .env desde %s", env_path)
            break

    settings = Settings(_env_file=[p for p in env_paths if p.exists()] or None)

    if not settings.transcend_api_key:
        logging.warning(
            "TRANSCEND_API_KEY no configurada. "
            "Establece la variable de entorno o crea ~/.transcend/.env"
        )

    return settings


settings = load_settings()