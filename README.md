# TRANSCEND MCP Server

Servidor MCP (Model Context Protocol) para la plataforma **TRANSCEND**.
Expone los microservicios reales de TRANSCEND (rutas, peajes, clima,
puntos de interés, tráfico y estaciones de servicio) como herramientas
invocables por asistentes de IA compatibles con MCP (Claude Desktop,
Cline, Continue, etc.).

## Funcionalidades

| Herramienta                  | Módulo   | Descripción                                               |
| ---------------------------- | -------- | --------------------------------------------------------- |
| `calculate_route`            | Route    | Ruta optimizada para camiones con restricciones y ADR     |
| `calculate_route_costs`      | Tolls    | Costos de ruta: peajes + combustible + mantenimiento + CO2|
| `get_current_weather`        | Weather  | Condiciones meteorológicas actuales en una ubicación      |
| `get_weather_forecast`       | Weather  | Pronóstico meteorológico para un rango de fechas          |
| `get_weather_alerts`         | Weather  | Alertas meteorológicas activas                            |
| `find_parking_by_location`   | POI      | Aparcamientos para camiones por coordenadas               |
| `find_parking_by_zipcode`    | POI      | Aparcamientos por código postal                           |
| `find_parking_by_province`   | POI      | Aparcamientos por provincia                               |
| `find_stations_nearby`       | Stations | Gasolineras cercanas a unas coordenadas                   |
| `search_stations`            | Stations | Gasolineras con filtros (tipo combustible, texto)         |
| `get_station_best_prices`    | Stations | Mejores precios de combustible cerca de una ubicación     |
| `get_blackspots_path`        | Traffic  | Zonas peligrosas (puntos negros) a lo largo de una ruta   |

## Servidores Reales (Production)

Cada módulo corre en su propio servidor:

| Módulo   | URL Base                                              |
| -------- | ----------------------------------------------------- |
| Route    | `https://api.transcend.es/route`                      |
| Tolls    | `https://back.transcend.cargoffer.com/tolls`          |
| Weather  | `https://back.transcend.cargoffer.com/weather/api`    |
| POI      | `https://back.transcend.cargoffer.com/poi`            |
| Traffic  | `https://traffic.transcend.cargoffer.com`             |
| Stations | `https://back.transcend.cargoffer.com/stations`       |

## Requisitos

- Python >= 3.10
- Una API key de TRANSCEND

## Instalación

```bash
cd /home/admin/code/transcend/transcend-mcp-server
pip install -e .
pip install -e ".[dev]"   # opcional: tests + lint
```

## Configuración

Crea un archivo `.env` en el directorio de trabajo o en `~/.transcend/.env`:

```env
TRANSCEND_API_KEY=tu-api-key-aqui
TRANSCEND_ENV=production
LOG_LEVEL=INFO
```

O exporta las variables de entorno directamente:

```bash
export TRANSCEND_API_KEY="tu-api-key"
export TRANSCEND_ENV="production"
```

### Entornos

| Variable          | Valor          | Descripción                                      |
| ----------------- | -------------- | ------------------------------------------------ |
| `TRANSCEND_ENV`   | `production`   | APIs de producción reales (default)              |
| `TRANSCEND_ENV`   | `release-dev`  | Servidores de release / pre-lanzamiento          |

## Uso

### Como servidor MCP (stdio)

```bash
python -m transcend_mcp
```

### Desde Claude Desktop

```json
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
```

### Como servidor HTTP/SSE

```bash
export MCP_HOST=0.0.0.0
export MCP_PORT=8100
python -m transcend_mcp
```

## Ejemplos de prompts para el LLM

> "Calcula una ruta para un camión de Vigo a Barcelona. El camión mide 4m de alto,
> 2.55m de ancho y pesa 40 toneladas. Incluye puntos negros."

> "¿Cuánto cuesta llevar una carga de 15 toneladas de Madrid a Valencia con
> un consumo medio de 35L/100km y gasóleo?"

> "Busca aparcamientos para camiones cerca de la Plaza España de Zaragoza."

> "¿Qué gasolineras hay cerca de la A-2 a la altura de Guadalajara? Dame los precios."

> "¿Hay zonas peligrosas en la ruta de Sevilla a Málaga?"

## Estructura del proyecto

```
transcend-mcp-server/
├── pyproject.toml
├── README.md
├── src/
│   └── transcend_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py        # Servidor FastMCP y bootstrap
│       ├── client.py        # Cliente HTTP multi-servidor (6 módulos)
│       ├── config.py        # Configuración con URLs por módulo y entorno
│       └── tools.py         # 12 herramientas MCP
└── tests/
    └── test_client.py       # Tests unitarios
```

## Desarrollo

```bash
# Tests
pytest

# Linting
ruff check src/

# Formato
ruff format src/
```

## Licencia

MIT
