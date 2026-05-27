# Operational MCP layer for European road transport intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![GitHub Release](https://img.shields.io/github/v/release/cargoffer/transcend-mcp-server)](https://github.com/cargoffer/transcend-mcp-server/releases)
[![GitHub Stars](https://img.shields.io/github/stars/cargoffer/transcend-mcp-server?style=social)](https://github.com/cargoffer/transcend-mcp-server)

**A route optimization MCP server** that connects AI agents (Claude Desktop, Cline, Continue, Cursor, etc.) to the TRANSCEND logistics intelligence platform — giving LLMs real-time access to truck route optimization, toll costs, weather, parking, traffic blackspots, and fuel station pricing across Spain and Europe.

> **What problem does it solve?** Truck logistics operators waste hours switching between Google Maps (not truck-aware), toll websites, weather apps, and fuel price spreadsheets. This MCP server consolidates 6 real-time logistics data sources into a single AI-callable interface so agents can plan routes, estimate costs, and assess risks in one step.
>
> **What makes it different?** Unlike generic mapping APIs, TRANSCEND is purpose-built for European **truck logistics API** needs — it respects ADR (dangerous goods) restrictions, truck height/width/weight limits, provides per-segment toll breakdowns with fuel and CO₂ costs, identifies dangerous blackspot zones, and locates truck-specific parking. It is the only unified MCP interface for European road logistics infrastructure.
>
> **What integration does it enable?** Any MCP-compatible client can invoke 12 logistics intelligence tools covering route optimization, toll cost estimation, weather conditions, POI parking, traffic blackspot analysis, and fuel station pricing — all from a single conversation with an LLM.
>
> **What does "easy integration" mean concretely?** `pip install` the package, set `TRANSCEND_API_KEY`, and add one JSON config block to Claude Desktop. No microservice orchestration, no multi-API key management, no custom middleware. Your AI assistant gains instant access to professional European **logistics document automation** and route intelligence.

---

## Why this MCP exists

European truck route planning is fragmented. Google Maps doesn't know truck height restrictions. Toll calculators are per-country. Weather alerts come from a third source. Fuel prices change hourly. Dispatchers manually juggle 5+ tabs to answer a single question like "what's the safest and cheapest route from Madrid to Frankfurt for a 4m-high refrigerated truck?"

This MCP server aggregates six TRANSCEND API microservices (Route, Tolls, Weather, POI, Traffic, Stations) behind a single MCP interface — making **European road transport** data accessible to AI agents through natural language. It transforms the agent from a chat interface into an operational logistics copilot.

---

## MCP Capabilities

- **12 MCP tools** across 6 logistics modules — organized by domain, not buried in code
- **Truck-aware route optimization** with ADR class restrictions, vehicle dimensions, and weight limits
- **Full cost breakdown** — tolls + fuel consumption + maintenance + CO₂ emissions per route
- **Real-time weather** — current conditions, multi-day forecasts, and active weather alerts along a corridor
- **Truck parking POI search** — by coordinates, zip code, or province (with capacity and amenities)
- **Traffic blackspot identification** — dangerous road zones along a planned route
- **Fuel station finder** — nearby stations, filtered search, and best-price ranking
- **Environment-aware configuration** — separate URLs for production vs. dev/release environments
- **HTTP/SSE and stdio transports** — works with all MCP clients out of the box
- **Pydantic-validated** inputs and outputs — Python 3.10+, httpx async client

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

## Directory structure

```
transcend-mcp-server/
├── pyproject.toml                  # Python 3.10+, dependencies: mcp, httpx, pydantic
├── src/transcend_mcp/
│   ├── server.py                   # FastMCP server bootstrap (stdio / HTTP/SSE)
│   ├── client.py                   # Multi-service HTTP client (6 backend APIs)
│   ├── config.py                   # Environment-aware URL resolution (prod / release-dev)
│   ├── tools.py                    # 12 MCP tool definitions with pydantic schemas
│   ├── __init__.py                 # Package init
│   └── __main__.py                 # Entry point for `python -m transcend_mcp`
└── tests/
    └── test_client.py              # Integration tests for client.py
```

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

## MCP protocol in action

**Calculate an optimized truck route:**

```bash
# With stdio transport, use any MCP client. For HTTP/SSE mode:
# First, connect to SSE endpoint, then send JSON-RPC messages

# Example using the JSON-RPC format over SSE (after establishing connection):
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "calculate_route",
  "params": {
    "origin": "Vigo, Spain",
    "destination": "Barcelona, Spain",
    "dimensions": {
      "height": 4.0,
      "width": 2.55,
      "weight": 40000,
      "adr_class": null
    }
  }
}
```

**Get route costs with real toll data:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "calculate_route_costs",
  "params": {
    "route_id": "route_abc_123",
    "fuel_consumption": 35,
    "fuel_type": "diesel",
    "include_co2": true
  }
}
```

**Find truck parking along the route:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "find_parking_by_location",
  "params": {
    "latitude": 41.6488,
    "longitude": -0.8891,
    "radius_km": 10
  }
}
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
| Tolls | `https://back.transcend.cargoffer.com/transcend/tolls` |
| POI | `https://back.transcend.cargoffer.com/transcend/poi` |
| Stations | `https://back.transcend.cargoffer.com/transcend/stations` |
| Weather | `https://back.transcend.cargoffer.com/transcend/weather` |
| Traffic | `https://back.transcend.cargoffer.com/transcend/traffic` |

---

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/
ruff format src/
```

---

## Semantic tags

`route optimization MCP` `truck logistics API` `MCP server` `Model Context Protocol` `European road transport` `logistics document automation` `TRANSCEND` `truck routing` `toll calculator` `fuel prices` `truck parking` `weather alerts` `traffic blackspots` `ADR restrictions` `CO2 emissions` `AI agents` `LLM tools` `supply chain` `Spain logistics` `Cargoffer` `easy MCP integration`

---

## License

MIT — see [LICENSE](LICENSE) file for details.

---

## Links

- **Repository:** [github.com/cargoffer/transcend-mcp-server](https://github.com/cargoffer/transcend-mcp-server)
- **Issues:** [github.com/cargoffer/transcend-mcp-server/issues](https://github.com/cargoffer/transcend-mcp-server/issues)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
