"""
Tests unitarios para el cliente HTTP de TRANSCEND.

Mockea las peticiones HTTP para verificar que el cliente forma
correctamente las URLs, los headers y los parámetros según los
endpoints reales de cada módulo.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from transcend_mcp.client import TranscendAPIError, TranscendClient


@pytest.fixture
def client():
    """Cliente con API key de prueba."""
    return TranscendClient(api_key="test-key-123")


def _get_call_info(mock):
    """Extrae args y kwargs del primer call del mock."""
    call = mock.call_args
    if call is None:
        return (), {}
    if hasattr(call, "args") and hasattr(call, "kwargs"):
        return call.args, call.kwargs
    if isinstance(call, tuple) and len(call) == 2:
        return call[0], call[1]
    return (), {}


# ==================================================================
#  ROUTE MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_calculate_route_basic(client):
    """Verifica que calculate_route envía los parámetros obligatorios."""
    mock_response = {"main": {"summary": {"time": "06:30", "length": 620.5}}}

    with patch.object(
        client._clients["route"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.calculate_route(
            origin_lat=42.2406, origin_lon=-8.7207,
            destiny_lat=41.3874, destiny_lon=2.1686,
        )

        assert result == mock_response
        mock_req.assert_awaited_once()
        _, kw_args = _get_call_info(mock_req)
        assert kw_args.get("method") == "GET"
        params = kw_args.get("params", {})
        assert params["origin_lat"] == 42.2406
        assert params["destiny_lat"] == 41.3874


@pytest.mark.asyncio
async def test_calculate_route_with_vehicle(client):
    """Verifica parámetros complejos (JSON-encoded)."""
    mock_response = {"main": {"summary": {"time": "06:30"}}}

    with patch.object(
        client._clients["route"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        vehicle_json = '{"width":2.55,"height":4.0,"weight":40000}'
        result = await client.calculate_route(
            origin_lat=40.4168, origin_lon=-3.7038,
            destiny_lat=41.3851, destiny_lon=2.1734,
            vehicle=vehicle_json,
            show_black_points=True,
        )

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["vehicle"] == vehicle_json
        assert params["show_black_points"] == "true"


# ==================================================================
#  TOLLS MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_calculate_route_costs(client):
    """Verifica el endpoint de costos de ruta (tolls)."""
    mock_response = {"costs": {"total_cost": 542.89, "toll": 87.25}}

    with patch.object(
        client._clients["tolls"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.calculate_route_costs(
            origin='{"lat":41.3851,"lng":2.1734}',
            destination='{"lat":40.4168,"lng":-3.7038}',
            avg_consumption=35,
            cargo_weight=15000,
            fuel_type="diesel",
        )

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        assert kw_args.get("method") == "GET"
        params = kw_args.get("params", {})
        assert "lat" in params["origin"]
        assert params["avg_consumption"] == 35
        assert params["fuel_type"] == "diesel"
        assert params["with_tolls"] == "true"


# ==================================================================
#  WEATHER MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_get_current_weather(client):
    mock_response = {"temperature": 22.5, "precipitationProbability": 10}

    with patch.object(
        client._clients["weather"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.get_current_weather(lat=40.4168, lon=-3.7038)

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["lat"] == 40.4168
        assert params["lon"] == -3.7038
        assert params["lang"] == "es"


# ==================================================================
#  POI MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_find_parking_by_location(client):
    mock_response = {"parkings": [{"name": "Parking Camiones A-2"}]}

    with patch.object(
        client._clients["poi"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.find_parking_by_location(lat=40.4168, lng=-3.7038, radius=5000)

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["lat"] == 40.4168
        assert params["radius"] == 5000


@pytest.mark.asyncio
async def test_find_parking_by_zipcode(client):
    mock_response = {"parkings": [{"name": "Parking Centro"}]}

    with patch.object(
        client._clients["poi"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.find_parking_by_zipcode(zipcode="28001", country="ES")

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["zipcode"] == "28001"
        assert params["country"] == "ES"


@pytest.mark.asyncio
async def test_find_parking_by_province(client):
    mock_response = {"parkings": [{"name": "Parking Madrid"}]}

    with patch.object(
        client._clients["poi"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.find_parking_by_province(province="Madrid")

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["province"] == "Madrid"


# ==================================================================
#  TRAFFIC MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_get_blackspots_path(client):
    mock_response = {"blackSpots": [{"dangerLevel": 75}]}

    with patch.object(
        client._clients["traffic"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.get_blackspots_path(
            points=[[-3.7038, 40.4168], [-3.7138, 40.4268]],
            min_danger_level=30,
        )

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        body = kw_args.get("json", {})
        assert len(body["points"]) == 2
        assert body["minDangerLevel"] == 30


# ==================================================================
#  STATIONS MODULE TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_find_stations_nearby(client):
    mock_response = {"stations": [{"label": "Repsol Madrid"}]}

    with patch.object(
        client._clients["stations"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(200, json=mock_response)

        result = await client.find_stations_nearby(lat=40.4168, lon=-3.7038)

        assert result == mock_response
        _, kw_args = _get_call_info(mock_req)
        params = kw_args.get("params", {})
        assert params["lat"] == 40.4168
        assert params["lon"] == -3.7038


# ==================================================================
#  ERROR HANDLING TESTS
# ==================================================================


@pytest.mark.asyncio
async def test_api_error(client):
    """Verifica que los errores HTTP se transforman en TranscendAPIError."""
    with patch.object(
        client._clients["route"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.return_value = httpx.Response(401, text='{"error": "Unauthorized"}')

        with pytest.raises(TranscendAPIError) as exc_info:
            await client.calculate_route(
                origin_lat=40.0, origin_lon=-3.0,
                destiny_lat=41.0, destiny_lon=2.0,
            )

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_timeout_error(client):
    """Verifica que los timeouts se capturan correctamente."""
    with patch.object(
        client._clients["poi"], "request", new_callable=AsyncMock
    ) as mock_req:
        mock_req.side_effect = httpx.TimeoutException("TimeOut")

        with pytest.raises(TranscendAPIError, match="TimeOut"):
            await client.find_parking_by_location(lat=40.0, lng=-3.0, radius=1000)


@pytest.mark.asyncio
async def test_headers_include_api_key():
    """Verifica que el header x-api-key se envía correctamente."""
    c = TranscendClient(api_key="secret-456")
    assert c._clients["route"].headers["x-api-key"] == "secret-456"


@pytest.mark.asyncio
async def test_close_client(client):
    """Verifica que close() cierra todas las sesiones HTTP."""
    with patch.object(
        client._clients["route"], "aclose", new_callable=AsyncMock
    ) as mock_close:
        await client.close()
        mock_close.assert_awaited_once()
