# transcend-mcp-server: Route Optimization & Logistics MCP Server for AI Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![GitHub Release](https://img.shields.io/github/v/release/cargoffer/transcend-mcp-server)](https://github.com/cargoffer/transcend-mcp-server/releases)
[![GitHub Stars](https://img.shields.io/github/stars/cargoffer/transcend-mcp-server?style=social)](https://github.com/cargoffer/transcend-mcp-server)

**Model Context Protocol (MCP) server** for the **TRANSCEND** logistics platform — exposes real APIs for route optimization, toll costs, weather, parking POIs, traffic blackspots, and fuel station pricing as tools for AI agents (Claude Desktop, Cline, Continue, Cursor, etc.).

---

## Quick Start

```bash
git clone https://github.com/cargoffer/transcend-mcp-server.git
cd transcend-mcp-server
pip install -e .
export TRANSCEND_API_KEY="your-api-key"
python -m transcend_mcp
```

By default runs on **stdio** (MCP transport). Set `MCP_HOST` / `MCP_PORT` for HTTP/SSE mode.

---

## What is this?

The TRANSCEND platform provides real-time logistics data across Spain and Europe. This MCP server bridges that data to AI agents through **12 tools across 6 modules**:

| Module | What it provides |
|--------|-----------------|
| 🗺️ **Route** | Optimized truck routes with ADR restrictions, vehicle dimensions, and weight limits |
| 💰 **Tolls** | Full cost breakdown: tolls + fuel + maintenance + CO₂ emissions |
| 🌤️ **Weather** | Current conditions, forecasts, and active weather alerts |
| 🅿️ **POI** | Truck parking locations by coordinates, zip code, or province |
| 🛑 **Traffic** | Dangerous blackspot zones along a route |
| ⛽ **Stations** | Fuel stations nearby, search with filters, best prices |

AI agents can query real logistics infrastructure — not static data — to plan routes, estimate costs, and assess risks for trucking operations.

---

## Tools

| Module | Tool | Description |
|--------|------|-------------|
| 🗺️ **Route** | `calculate_route` | Optimized truck route with ADR, height, width, weight constraints |
| 💰 **Tolls** | `calculate_route_costs` | Fuel + tolls + maintenance + CO₂ cost estimation |
| 🌤️ **Weather** | `get_current_weather` | Real-time weather at a location |
| | `get_weather_forecast` | Forecast for a date range |
| | `get_weather_alerts` | Active weather warnings |
| 🅿️ **POI** | `find_parking_by_location` | Truck parking near coordinates |
| | `find_parking_by_zipcode` | Parking by postal code |
| | `find_parking_by_province` | Parking by province |
| 🛑 **Traffic** | `get_blackspots_path` | Dangerous zones along a route |
| ⛽ **Stations** | `find_stations_nearby` | Fuel stations near coordinates |
| | `search_stations` | Filter stations by fuel type, text search |
| | `get_station_best_prices` | Best fuel prices near a location |

---

## Installation

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "transcend": {
      "command": "python",
      "args": ["-m", "transcend_mcp"],
      "env": {
        "TRANSCEND_API_KEY": "your-api-key",
        "TRANSCEND_ENV": "production"
      }
    }
  }
}
```

### Cursor

**Cursor Settings → Features → MCP Servers → Add New**:

```
Name:   transcend
Type:   command
Command: python -m transcend_mcp
Env:    TRANSCEND_API_KEY=your-api-key, TRANSCEND_ENV=production
```

### Direct HTTP / SSE

```bash
export MCP_HOST=0.0.0.0
export MCP_PORT=8100
python -m transcend_mcp

# Then connect SSE at http://localhost:8100/sse
```

---

## Example Prompts for AI Agents

> "Calculate an optimized truck route from Vigo to Barcelona. The truck is 4m high, 2.55m wide, 40 tons. Include blackspot warnings."

> "What's the total cost of a 15-ton load from Madrid to Valencia with average fuel consumption of 35L/100km using diesel?"

> "Find truck parking near Plaza España in Zaragoza."

> "What fuel stations are near the A-2 highway at Guadalajara? Show me the best prices."

> "Are there any dangerous zones on the route from Seville to Málaga?"

> "What's the weather forecast along the A-3 from Madrid to Valencia for tomorrow? Any alerts?"

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRANSCEND_API_KEY` | ✔ | — | Your TRANSCEND API key |
| `TRANSCEND_ENV` | | `production` | `production` or `release-dev` |
| `LOG_LEVEL` | | `INFO` | Logging verbosity |
| `MCP_HOST` | | `localhost` | HTTP/SSE bind address |
| `MCP_PORT` | | `8100` | HTTP/SSE port |

### Production Microservice URLs

| Module | Prod URL |
|--------|----------|
| Route | `https://api.transcend.es/route` |
| Tolls | `https://back.transcend.cargoffer.com/tolls` |
| Weather | `https://back.transcend.cargoffer.com/weather/api` |
| POI | `https://back.transcend.cargoffer.com/poi` |
| Traffic | `https://traffic.transcend.cargoffer.com` |
| Stations | `https://back.transcend.cargoffer.com/stations` |

---

## Project Structure

```
transcend-mcp-server/
├── pyproject.toml
├── src/transcend_mcp/
│   ├── server.py        # FastMCP server bootstrap
│   ├── client.py        # Multi-service HTTP client (6 backends)
│   ├── config.py        # Environment-aware URL resolution
│   ├── tools.py         # 12 MCP tool definitions
│   ├── __init__.py
│   └── __main__.py
└── tests/
    └── test_client.py
```

---

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/
ruff format src/
```

---

## License

MIT — see [LICENSE](LICENSE) file for details.

---

## Links

- **Repository:** [github.com/cargoffer/transcend-mcp-server](https://github.com/cargoffer/transcend-mcp-server)
- **Issues:** [github.com/cargoffer/transcend-mcp-server/issues](https://github.com/cargoffer/transcend-mcp-server/issues)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
