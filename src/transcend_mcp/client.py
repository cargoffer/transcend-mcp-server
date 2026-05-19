"""
Cliente HTTP multi-servidor para la API REST de TRANSCEND.

Cada módulo de TRANSCEND corre en su propio servidor. Este cliente
mantiene un mapa de cliente HTTP por módulo y expone métodos
que invocan el endpoint correcto en el servidor adecuado.
"""

import logging
from typing import Any

import httpx

from transcend_mcp.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0  # segundos


# ── Excepciones ──────────────────────────────────────────────────────────


class TranscendAPIError(Exception):
    """Error genérico de la API TRANSCEND."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


# ── Cliente multi-servidor ───────────────────────────────────────────────


class TranscendClient:
    """
    Cliente HTTP para los distintos módulos de TRANSCEND.

    Cada módulo (route, tolls, weather, poi, traffic, stations) se
    resuelve contra su propio servidor según la configuración de
    entornos (production / release-dev).

    La autenticación se realiza mediante:
      - JWT Bearer Token (Authorization: Bearer <token>)
      - API Key (x-api-key: <api-key>)
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.transcend_api_key

        # Construimos un cliente HTTP por módulo
        self._clients: dict[str, httpx.AsyncClient] = {}
        for module_name in ("route", "tolls", "weather", "poi", "traffic", "stations"):
            base_url = settings.module_url(module_name)
            if base_url:
                self._clients[module_name] = httpx.AsyncClient(
                    base_url=base_url.rstrip("/"),
                    timeout=DEFAULT_TIMEOUT,
                    headers=self._build_headers(),
                )

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    # ------------------------------------------------------------------
    # Petición base (enruta al módulo indicado)
    # ------------------------------------------------------------------

    async def _request(
        self,
        module: str,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Realiza una petición HTTP contra el servidor del *module* indicado.

        Lanza TranscendAPIError si el servidor devuelve un error HTTP.
        """
        client = self._clients.get(module)
        if client is None:
            raise TranscendAPIError(f"Módulo '{module}' no configurado (sin URL base)")

        url = f"/{path.lstrip('/')}"
        logger.debug(
            "[%s] %s %s params=%s body=%s", module, method.upper(), url, params, json_body
        )

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
            )
        except httpx.TimeoutException as exc:
            raise TranscendAPIError(
                f"TimeOut tras {DEFAULT_TIMEOUT}s en [{module}] {method} {path}"
            ) from exc
        except httpx.RequestError as exc:
            raise TranscendAPIError(
                f"Error de conexión en [{module}]: {exc}"
            ) from exc

        if not response.is_success:
            body_text = response.text[:500] if response.text else ""
            logger.error(
                "Error [%s] %s %s -> %s: %s",
                module, method.upper(), url, response.status_code, body_text,
            )
            raise TranscendAPIError(
                f"La API [{module}] respondió con código {response.status_code}",
                status_code=response.status_code,
                response_body=body_text,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise TranscendAPIError(
                f"Respuesta no JSON desde [{module}] {method} {path}: "
                f"{response.text[:200]}"
            ) from exc

    # ==================================================================
    #  ROUTE MODULE  —  https://api.transcend.es/route
    # ==================================================================

    async def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        destiny_lat: float,
        destiny_lon: float,
        waypoints: str | None = None,
        avoid_points: str | None = None,
        vehicle: str | None = None,
        driver: str | None = None,
        merchandise: str | None = None,
        date: str | None = None,
        map_layers: str | None = None,
        show_black_points: bool | None = None,
    ) -> dict[str, Any]:
        """
        Calcula una ruta optimizada para camiones.

        GET /api/route

        Los parámetros complejos (waypoints, vehicle, driver, merchandise,
        date, map_layers) se pasan como strings JSON-encoded.
        """
        params: dict[str, Any] = {
            "origin_lat": origin_lat,
            "origin_lon": origin_lon,
            "destiny_lat": destiny_lat,
            "destiny_lon": destiny_lon,
        }
        if waypoints is not None:
            params["waypoints"] = waypoints
        if avoid_points is not None:
            params["avoid_points"] = avoid_points
        if vehicle is not None:
            params["vehicle"] = vehicle
        if driver is not None:
            params["driver"] = driver
        if merchandise is not None:
            params["merchandise"] = merchandise
        if date is not None:
            params["date"] = date
        if map_layers is not None:
            params["map_layers"] = map_layers
        if show_black_points is not None:
            params["show_black_points"] = str(show_black_points).lower()

        return await self._request("route", "GET", "/api/route", params=params)

    async def get_route_health(self) -> dict[str, Any]:
        """GET /health — Health check del módulo route."""
        return await self._request("route", "GET", "/health")

    async def get_route_test(self) -> dict[str, Any]:
        """GET /test — Test endpoint del módulo route."""
        return await self._request("route", "GET", "/test")

    # ==================================================================
    #  TOLLS MODULE  —  https://back.transcend.cargoffer.com/tolls
    # ==================================================================

    async def calculate_route_costs(
        self,
        origin: str,
        destination: str,
        with_tolls: bool = True,
        avg_consumption: float | None = None,
        cargo_weight: float | None = None,
        fuel_type: str = "diesel",
        departure: str | None = None,
        arrival: str | None = None,
        with_points: bool = False,
    ) -> dict[str, Any]:
        """
        Calcula los costes completos de una ruta de transporte.

        GET /costs

        Incluye peajes, combustible, mantenimiento, tiempo de conducción
        y emisiones de CO2.

        Args:
            origin: JSON string {"lat":..., "lng":...}
            destination: JSON string {"lat":..., "lng":...}
            with_tolls: Incluir desglose detallado de peajes
            avg_consumption: Consumo medio (L/100km), default 35
            cargo_weight: Peso de la carga en kg
            fuel_type: diesel | gasoline | gnv
            departure: ISO 8601 fecha de salida
            arrival: ISO 8601 fecha de llegada estimada
            with_points: Incluir puntos intermedios para mapas
        """
        params: dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "with_tolls": str(with_tolls).lower(),
            "fuel_type": fuel_type,
            "with_points": str(with_points).lower(),
        }
        if avg_consumption is not None:
            params["avg_consumption"] = avg_consumption
        if cargo_weight is not None:
            params["cargo_weight"] = cargo_weight
        if departure is not None:
            params["departure"] = departure
        if arrival is not None:
            params["arrival"] = arrival

        return await self._request("tolls", "GET", "/costs", params=params)

    # ==================================================================
    #  WEATHER MODULE  —  https://back.transcend.cargoffer.com/weather/api
    # ==================================================================

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Obtiene las condiciones meteorológicas actuales en una ubicación.

        GET /current
        """
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        return await self._request("weather", "GET", "/current", params=params)

    async def get_weather_forecast(
        self,
        lat: float,
        lon: float,
        start: str,
        end: str,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Obtiene pronóstico meteorológico para un período.

        GET /forecast
        """
        params: dict[str, Any] = {
            "lat": lat, "lon": lon,
            "start": start, "end": end,
            "lang": lang,
        }
        return await self._request("weather", "GET", "/forecast", params=params)

    async def get_weather_alerts(
        self,
        lat: float,
        lon: float,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Obtiene alertas meteorológicas activas en una ubicación.

        GET /alerts/current
        """
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        return await self._request("weather", "GET", "/alerts/current", params=params)

    # ==================================================================
    #  POI MODULE  —  https://back.transcend.cargoffer.com/poi
    # ==================================================================

    async def find_parking_by_location(
        self,
        lat: float,
        lng: float,
        radius: float,
    ) -> dict[str, Any]:
        """
        Busca aparcamientos para camiones por coordenadas.

        GET /parking/location
        """
        params: dict[str, Any] = {"lat": lat, "lng": lng, "radius": radius}
        return await self._request("poi", "GET", "/parking/location", params=params)

    async def find_parking_by_zipcode(
        self,
        zipcode: str,
        country: str = "ES",
    ) -> dict[str, Any]:
        """
        Busca aparcamientos por código postal.

        GET /parking/zipcode
        """
        params: dict[str, Any] = {"zipcode": zipcode, "country": country}
        return await self._request("poi", "GET", "/parking/zipcode", params=params)

    async def find_parking_by_province(
        self,
        province: str,
    ) -> dict[str, Any]:
        """
        Busca aparcamientos por provincia.

        GET /parking/province
        """
        params: dict[str, Any] = {"province": province}
        return await self._request("poi", "GET", "/parking/province", params=params)

    async def find_parking_nearby(
        self,
        lat: float,
        lng: float,
        radius: float | None = None,
    ) -> dict[str, Any]:
        """
        Busca aparcamientos cercanos a unas coordenadas.

        GET /parking/nearby
        """
        params: dict[str, Any] = {"lat": lat, "lng": lng}
        if radius is not None:
            params["radius"] = radius
        return await self._request("poi", "GET", "/parking/nearby", params=params)

    async def find_restaurants_nearby(
        self,
        lat: float,
        lng: float,
        radius: float | None = None,
    ) -> dict[str, Any]:
        """GET /restaurant/nearby — Restaurantes cercanos."""
        params: dict[str, Any] = {"lat": lat, "lng": lng}
        if radius is not None:
            params["radius"] = radius
        return await self._request("poi", "GET", "/restaurant/nearby", params=params)

    async def find_workshops_nearby(
        self,
        lat: float,
        lng: float,
        radius: float | None = None,
    ) -> dict[str, Any]:
        """GET /workshop/nearby — Talleres cercanos."""
        params: dict[str, Any] = {"lat": lat, "lng": lng}
        if radius is not None:
            params["radius"] = radius
        return await self._request("poi", "GET", "/workshop/nearby", params=params)

    async def find_showers_nearby(
        self,
        lat: float,
        lng: float,
        radius: float | None = None,
        shower_type: str | None = None,
    ) -> dict[str, Any]:
        """GET /shower/nearby — Duchas/áreas de descanso cercanas."""
        params: dict[str, Any] = {"lat": lat, "lng": lng}
        if radius is not None:
            params["radius"] = radius
        if shower_type is not None:
            params["type"] = shower_type
        return await self._request("poi", "GET", "/shower/nearby", params=params)

    # ==================================================================
    #  TRAFFIC MODULE  —  https://traffic.transcend.cargoffer.com
    # ==================================================================

    async def get_blackspots_path(
        self,
        points: list[list[float]],
        min_danger_level: int = 30,
    ) -> dict[str, Any]:
        """
        Obtiene zonas peligrosas a lo largo de una ruta.

        POST /blackspots/path

        Args:
            points: Lista de puntos [[lon, lat], [lon, lat], ...]
            min_danger_level: Nivel mínimo de peligrosidad (0-100)
        """
        body: dict[str, Any] = {
            "points": points,
            "minDangerLevel": min_danger_level,
        }
        return await self._request("traffic", "POST", "/blackspots/path", json_body=body)

    async def get_blackspots_area(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        min_danger_level: int | None = None,
    ) -> dict[str, Any]:
        """GET /blackspots/area — Puntos negros en un área."""
        params: dict[str, Any] = {"lat": lat, "lon": lon}
        if radius is not None:
            params["radius"] = radius
        if min_danger_level is not None:
            params["minDangerLevel"] = min_danger_level
        return await self._request("traffic", "GET", "/blackspots/area", params=params)

    async def get_traffic_events_nearby(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """GET /events/nearby — Eventos de tráfico cercanos."""
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        if radius is not None:
            params["radius"] = radius
        return await self._request("traffic", "GET", "/events/nearby", params=params)

    async def get_radars_nearby(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """GET /radar/nearby — Radares cercanos."""
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        if radius is not None:
            params["radius"] = radius
        return await self._request("traffic", "GET", "/radar/nearby", params=params)

    # ==================================================================
    #  STATIONS MODULE  —  https://back.transcend.cargoffer.com/stations
    # ==================================================================

    async def find_stations_nearby(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Busca estaciones de servicio cercanas a unas coordenadas.

        GET /stations/nearby
        """
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        if radius is not None:
            params["radius"] = radius
        return await self._request("stations", "GET", "/stations/nearby", params=params)

    async def search_stations(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        fuel_type: str | None = None,
        query: str | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Busca estaciones de servicio con filtros adicionales.

        GET /stations/search
        """
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        if radius is not None:
            params["radius"] = radius
        if fuel_type is not None:
            params["fuelType"] = fuel_type
        if query is not None:
            params["q"] = query
        return await self._request("stations", "GET", "/stations/search", params=params)

    async def get_station_best_prices(
        self,
        lat: float,
        lon: float,
        radius: float | None = None,
        fuel_type: str | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """GET /stations/best-prices — Mejores precios de combustible."""
        params: dict[str, Any] = {"lat": lat, "lon": lon, "lang": lang}
        if radius is not None:
            params["radius"] = radius
        if fuel_type is not None:
            params["fuelType"] = fuel_type
        return await self._request("stations", "GET", "/stations/best-prices", params=params)

    async def get_station_by_id(
        self,
        station_id: str,
        lang: str = "es",
    ) -> dict[str, Any]:
        """GET /stations/{id} — Detalle de una estación."""
        return await self._request(
            "stations", "GET", f"/stations/{station_id}", params={"lang": lang}
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Cierra todas las sesiones HTTP."""
        for name, client in self._clients.items():
            try:
                await client.aclose()
            except Exception:
                logger.debug("Error al cerrar cliente '%s'", name, exc_info=True)
