"""
Herramientas MCP de TRANSCEND.

Cada función decorada con @tool se convierte en una herramienta
que los asistentes de IA pueden descubrir e invocar a través
del protocolo MCP.

Las herramientas siguen fielmente los endpoints reales de la API
según los OpenAPI specs de cada módulo.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from transcend_mcp.client import TranscendAPIError, TranscendClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: TranscendClient) -> None:
    """
    Registra todas las herramientas MCP en el servidor.
    """

    # ==================================================================
    #  1. calculate_route  (Route Module)
    # ==================================================================
    @mcp.tool(
        name="calculate_route",
        description=(
            "Calcula una ruta optimizada para camiones entre dos coordenadas. "
            "Considera restricciones del vehículo (altura, anchura, peso), "
            "normativa EU de tiempos de conducción, puntos negros de tráfico "
            "y mercancías peligrosas (ADR). "
            "Parámetros complejos (vehicle, driver, merchandise, map_layers) "
            "deben pasarse como JSON string."
        ),
    )
    async def calculate_route(
        origin_lat: float,
        origin_lon: float,
        destiny_lat: float,
        destiny_lon: float,
        waypoints: str | None = None,
        vehicle: str | None = None,
        driver: str | None = None,
        merchandise: str | None = None,
        date: str | None = None,
        map_layers: str | None = None,
        show_black_points: bool | None = None,
    ) -> str:
        """
        Calcula una ruta optimizada para transporte de mercancías.

        Args:
            origin_lat: Latitud del origen (grados decimales, ej: 42.2406)
            origin_lon: Longitud del origen (grados decimales, ej: -8.7207)
            destiny_lat: Latitud del destino (grados decimales)
            destiny_lon: Longitud del destino (grados decimales)
            waypoints: JSON string con array de waypoints intermedios.
                       Ej: [{"position":[40.5,-3.5],"customBreakMinutes":30}]
            vehicle: JSON string con datos del vehículo.
                     Ej: {"width":2.55,"height":4.0,"weight":40000,"consumption":32}
            driver: JSON string con estado de horas del conductor.
                    Ej: {"hoursStatus":{"remainingWeeklyHours":56,"remainingDayHours":9}}
            merchandise: JSON string con info de mercancía.
                         Ej: {"hsCode":"3301","weight":20000,"isADR":true}
            date: JSON string con tipo de fecha y fecha ISO 8601.
                  Ej: {"type":"departure","date":"2025-01-15T08:00:00Z"}
            map_layers: JSON string con opciones de ruta.
                        Ej: {"avoidTolls":false,"calculateStops":true}
            show_black_points: Incluir puntos negros en la respuesta.
        """
        try:
            result = await client.calculate_route(
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                destiny_lat=destiny_lat,
                destiny_lon=destiny_lon,
                waypoints=waypoints,
                vehicle=vehicle,
                driver=driver,
                merchandise=merchandise,
                date=date,
                map_layers=map_layers,
                show_black_points=show_black_points,
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("calculate_route", e)

    # ==================================================================
    #  2. calculate_route_costs  (Tolls Module)
    # ==================================================================
    @mcp.tool(
        name="calculate_route_costs",
        description=(
            "Calcula los costos completos de una ruta de transporte: peajes, "
            "combustible, mantenimiento, tiempo de conducción y emisiones de CO2. "
            "Los parámetros origin y destination se pasan como JSON string "
            'con el formato {"lat":...,"lng":...}. '
            "Ideal para presupuestos y planificación de flotas."
        ),
    )
    async def calculate_route_costs(
        origin: str,
        destination: str,
        with_tolls: bool = True,
        avg_consumption: float | None = None,
        cargo_weight: float | None = None,
        fuel_type: str = "diesel",
        departure: str | None = None,
        arrival: str | None = None,
    ) -> str:
        """
        Calcula costos de ruta (tolls module).

        Args:
            origin: JSON string con coordenadas de origen.
                    Ej: {"lat":41.3851,"lng":2.1734}
            destination: JSON string con coordenadas de destino.
                         Ej: {"lat":40.4168,"lng":-3.7038}
            with_tolls: Incluir desglose detallado de peajes.
            avg_consumption: Consumo medio en L/100km (default: 35).
            cargo_weight: Peso de la carga en kg.
            fuel_type: Tipo de combustible: diesel | gasoline | gnv.
            departure: Fecha/hora de salida (ISO 8601).
                       Ej: "2025-05-15T08:00:00"
            arrival: Fecha/hora de llegada estimada (ISO 8601).
        """
        try:
            result = await client.calculate_route_costs(
                origin=origin,
                destination=destination,
                with_tolls=with_tolls,
                avg_consumption=avg_consumption,
                cargo_weight=cargo_weight,
                fuel_type=fuel_type,
                departure=departure,
                arrival=arrival,
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("calculate_route_costs", e)

    # ==================================================================
    #  3. get_current_weather  (Weather Module)
    # ==================================================================
    @mcp.tool(
        name="get_current_weather",
        description=(
            "Obtiene las condiciones meteorológicas actuales en una ubicación "
            "geográfica: temperatura, precipitación, viento, nivel de peligro "
            "y alertas. Útil para planificar rutas seguras."
        ),
    )
    async def get_current_weather(
        lat: float,
        lon: float,
        lang: str = "es",
    ) -> str:
        """
        Obtiene el tiempo meteorológico actual.

        Args:
            lat: Latitud (grados decimales, -90 a 90).
            lon: Longitud (grados decimales, -180 a 180).
            lang: Idioma de respuesta (es, en, fr, de, pt).
        """
        if not (-90 <= lat <= 90):
            return _error_response(
                "get_current_weather",
                ValueError(f"Latitud fuera de rango: {lat}"),
            )
        if not (-180 <= lon <= 180):
            return _error_response(
                "get_current_weather",
                ValueError(f"Longitud fuera de rango: {lon}"),
            )
        try:
            result = await client.get_current_weather(lat=lat, lon=lon, lang=lang)
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("get_current_weather", e)

    # ==================================================================
    #  4. find_parking_by_location  (POI Module)
    # ==================================================================
    @mcp.tool(
        name="find_parking_by_location",
        description=(
            "Busca aparcamientos para camiones cerca de unas coordenadas "
            "geográficas. Devuelve nombre, dirección, coordenadas y "
            "características de cada aparcamiento."
        ),
    )
    async def find_parking_by_location(
        lat: float,
        lng: float,
        radius: float,
    ) -> str:
        """
        Busca aparcamientos por coordenadas.

        Args:
            lat: Latitud del centro de búsqueda.
            lng: Longitud del centro de búsqueda.
            radius: Radio de búsqueda en metros.
        """
        try:
            result = await client.find_parking_by_location(lat=lat, lng=lng, radius=radius)
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("find_parking_by_location", e)

    # ==================================================================
    #  5. find_parking_by_zipcode  (POI Module)
    # ==================================================================
    @mcp.tool(
        name="find_parking_by_zipcode",
        description=(
            "Busca aparcamientos para camiones por código postal y país. "
            "Útil cuando se conoce el código postal pero no las coordenadas exactas."
        ),
    )
    async def find_parking_by_zipcode(
        zipcode: str,
        country: str = "ES",
    ) -> str:
        """
        Busca aparcamientos por código postal.

        Args:
            zipcode: Código postal (ej: "28001").
            country: Código de país ISO 3166-1 alpha-2 (ej: "ES", "FR", "PT").
        """
        try:
            result = await client.find_parking_by_zipcode(zipcode=zipcode, country=country)
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("find_parking_by_zipcode", e)

    # ==================================================================
    #  6. find_parking_by_province  (POI Module)
    # ==================================================================
    @mcp.tool(
        name="find_parking_by_province",
        description=(
            "Busca aparcamientos para camiones en una provincia específica. "
            "Ej: 'Madrid', 'Barcelona', 'Valencia'."
        ),
    )
    async def find_parking_by_province(
        province: str,
    ) -> str:
        """
        Busca aparcamientos por provincia.

        Args:
            province: Nombre de la provincia (ej: "Madrid", "Barcelona").
        """
        try:
            result = await client.find_parking_by_province(province=province)
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("find_parking_by_province", e)

    # ==================================================================
    #  7. find_stations_nearby  (Stations Module)
    # ==================================================================
    @mcp.tool(
        name="find_stations_nearby",
        description=(
            "Busca estaciones de servicio cercanas a unas coordenadas. "
            "Devuelve nombre, dirección, tipos de combustible disponibles, "
            "precios y distancia. Esencial para planificar repostajes en ruta."
        ),
    )
    async def find_stations_nearby(
        lat: float,
        lon: float,
        radius: float | None = None,
        lang: str = "es",
    ) -> str:
        """
        Busca gasolineras cercanas.

        Args:
            lat: Latitud del centro de búsqueda.
            lon: Longitud del centro de búsqueda.
            radius: Radio de búsqueda en metros (default: 25000).
            lang: Idioma de respuesta (es, en, fr, de, pt).
        """
        try:
            result = await client.find_stations_nearby(
                lat=lat, lon=lon, radius=radius, lang=lang
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("find_stations_nearby", e)

    # ==================================================================
    #  8. search_stations  (Stations Module)
    # ==================================================================
    @mcp.tool(
        name="search_stations",
        description=(
            "Busca estaciones de servicio con filtros avanzados: por ubicación, "
            "radio, tipo de combustible y texto de búsqueda. "
            "Útil para encontrar una marca o tipo de combustible específico."
        ),
    )
    async def search_stations(
        lat: float,
        lon: float,
        radius: float | None = None,
        fuel_type: str | None = None,
        query: str | None = None,
        lang: str = "es",
    ) -> str:
        """
        Busca estaciones de servicio con filtros.

        Args:
            lat: Latitud del centro de búsqueda.
            lon: Longitud del centro de búsqueda.
            radius: Radio de búsqueda en metros.
            fuel_type: Tipo de combustible (diesel_regular, diesel_premium,
                       gasoline_95, gasoline_98, gnc, gnl, gpl, etc.).
            query: Texto de búsqueda (nombre, marca, etc.).
            lang: Idioma de respuesta.
        """
        try:
            result = await client.search_stations(
                lat=lat, lon=lon, radius=radius,
                fuel_type=fuel_type, query=query, lang=lang,
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("search_stations", e)

    # ==================================================================
    #  9. get_blackspots_path  (Traffic Module)
    # ==================================================================
    @mcp.tool(
        name="get_blackspots_path",
        description=(
            "Obtiene zonas de alta peligrosidad (puntos negros) a lo largo "
            "de una ruta definida por una lista de puntos GPS. "
            "Cada punto se pasa como [longitud, latitud]. "
            "Devuelve nivel de peligrosidad (0-100) y descripción de cada zona."
        ),
    )
    async def get_blackspots_path(
        points: list[list[float]],
        min_danger_level: int = 30,
    ) -> str:
        """
        Obtiene puntos negros en una ruta.

        Args:
            points: Lista de puntos GPS en formato [[lon, lat], [lon, lat], ...].
                    Mínimo 2 puntos.
            min_danger_level: Nivel mínimo de peligrosidad (0-100).
                              Solo se devuelven puntos con nivel >= este valor.
        """
        if len(points) < 2:
            return _error_response(
                "get_blackspots_path",
                ValueError("Se necesitan al menos 2 puntos para definir una ruta."),
            )
        min_danger_level = max(0, min(100, min_danger_level))
        try:
            result = await client.get_blackspots_path(
                points=points,
                min_danger_level=min_danger_level,
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("get_blackspots_path", e)

    # ==================================================================
    #  10. get_station_best_prices  (Stations Module)
    # ==================================================================
    @mcp.tool(
        name="get_station_best_prices",
        description=(
            "Obtiene las mejores (más bajos) precios de combustible cerca "
            "de una ubicación, filtrados opcionalmente por tipo de combustible."
        ),
    )
    async def get_station_best_prices(
        lat: float,
        lon: float,
        radius: float | None = None,
        fuel_type: str | None = None,
        lang: str = "es",
    ) -> str:
        """
        Busca los mejores precios de combustible.

        Args:
            lat: Latitud del centro de búsqueda.
            lon: Longitud del centro de búsqueda.
            radius: Radio de búsqueda en metros.
            fuel_type: Tipo de combustible (diesel_regular, gasoline_95, etc.).
            lang: Idioma de respuesta.
        """
        try:
            result = await client.get_station_best_prices(
                lat=lat, lon=lon, radius=radius,
                fuel_type=fuel_type, lang=lang,
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("get_station_best_prices", e)

    # ==================================================================
    #  11. get_weather_forecast  (Weather Module)
    # ==================================================================
    @mcp.tool(
        name="get_weather_forecast",
        description=(
            "Obtiene el pronóstico meteorológico detallado para una ubicación "
            "en un rango de fechas. Devuelve temperatura, precipitación, "
            "viento y nivel de peligro para cada día."
        ),
    )
    async def get_weather_forecast(
        lat: float,
        lon: float,
        start: str,
        end: str,
        lang: str = "es",
    ) -> str:
        """
        Obtiene pronóstico meteorológico.

        Args:
            lat: Latitud.
            lon: Longitud.
            start: Fecha de inicio (YYYY-MM-DD).
            end: Fecha de fin (YYYY-MM-DD).
            lang: Idioma (es, en, fr, de, pt).
        """
        try:
            result = await client.get_weather_forecast(
                lat=lat, lon=lon, start=start, end=end, lang=lang
            )
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("get_weather_forecast", e)

    # ==================================================================
    #  12. get_weather_alerts  (Weather Module)
    # ==================================================================
    @mcp.tool(
        name="get_weather_alerts",
        description=(
            "Obtiene alertas meteorológicas activas en una ubicación. "
            "Devuelve nivel de alerta, tipo y descripción del evento climático."
        ),
    )
    async def get_weather_alerts(
        lat: float,
        lon: float,
        lang: str = "es",
    ) -> str:
        """
        Obtiene alertas meteorológicas activas.

        Args:
            lat: Latitud.
            lon: Longitud.
            lang: Idioma (es, en, fr, de, pt).
        """
        try:
            result = await client.get_weather_alerts(lat=lat, lon=lon, lang=lang)
            return _format_json(result)
        except TranscendAPIError as e:
            return _error_response("get_weather_alerts", e)

    logger.info("Herramientas MCP registradas: 12 herramientas")


# ======================================================================
# Utilidades
# ======================================================================


def _format_json(data: Any) -> str:
    """Formatea un objeto Python como JSON legible."""
    import json

    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _error_response(tool_name: str, error: Exception) -> str:
    """
    Devuelve un mensaje de error formateado para el LLM.
    """
    if isinstance(error, TranscendAPIError):
        parts = [f"  • Mensaje: {error.args[0] if error.args else 'Desconocido'}"]
        if error.status_code:
            parts.insert(0, f"  • Código HTTP: {error.status_code}")
        if error.response_body:
            parts.append(f"  • Respuesta: {error.response_body[:300]}")
        detail = "\n".join(parts)
        logger.warning("Error en herramienta '%s':\n%s", tool_name, detail)
        return (
            f"Error al ejecutar '{tool_name}':\n{detail}\n\n"
            "Verifica que los parámetros sean correctos y que la API key sea válida."
        )

    logger.error("Error interno en herramienta '%s': %s", tool_name, error)
    return (
        f"Error interno en la herramienta '{tool_name}': {error}\n\n"
        "Revisa la conexión con los servidores de TRANSCEND."
    )
