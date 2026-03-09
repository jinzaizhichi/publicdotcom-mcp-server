"""Tests for read-only MCP tools."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from publicdotcom_mcp_server.server import (
    get_accounts,
    get_history,
    get_instrument,
    get_option_greeks,
    get_order,
    get_orders,
    get_portfolio,
    get_quotes,
)


def _make_model(data: dict) -> MagicMock:
    """Create a mock Pydantic-like model with model_dump()."""
    m = MagicMock()
    m.model_dump.return_value = data
    return m


class TestGetAccounts:
    async def test_returns_serialized_accounts(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_accounts = AsyncMock(return_value=_make_model({"accounts": []}))

        result = await get_accounts()
        assert '"accounts"' in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_accounts = AsyncMock(side_effect=Exception("network timeout"))

        result = await get_accounts()
        assert "Error" in result
        assert "network timeout" in result

    async def test_missing_secret_returns_error(self, monkeypatch, patch_get_client):
        # When _get_client raises (e.g., missing secret), tool returns error string
        from unittest.mock import patch as mock_patch
        with mock_patch(
            "publicdotcom_mcp_server.server._get_client",
            side_effect=RuntimeError("PUBLIC_COM_SECRET is not set"),
        ):
            result = await get_accounts()
        assert "Error" in result
        assert "PUBLIC_COM_SECRET" in result


class TestGetPortfolio:
    async def test_returns_serialized_portfolio(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_portfolio = AsyncMock(
            return_value=_make_model({"equity": "10000.00"})
        )

        result = await get_portfolio()
        assert '"equity"' in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_portfolio = AsyncMock(side_effect=Exception("API error"))

        result = await get_portfolio()
        assert "Error" in result


class TestGetOrders:
    async def test_returns_only_open_orders(self, patch_get_client):
        mock_client = patch_get_client
        mock_order = _make_model({"order_id": "abc-123", "status": "OPEN"})
        mock_portfolio = MagicMock()
        mock_portfolio.open_orders = [mock_order]
        mock_client.get_portfolio = AsyncMock(return_value=mock_portfolio)

        result = await get_orders()
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["order_id"] == "abc-123"

    async def test_returns_empty_list_when_no_open_orders(self, patch_get_client):
        mock_client = patch_get_client
        mock_portfolio = MagicMock()
        mock_portfolio.open_orders = None
        mock_client.get_portfolio = AsyncMock(return_value=mock_portfolio)

        result = await get_orders()
        assert result == "[]"

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_portfolio = AsyncMock(side_effect=Exception("timeout"))

        result = await get_orders()
        assert "Error" in result


class TestGetOrder:
    async def test_returns_order_details(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_order = AsyncMock(
            return_value=_make_model({"order_id": "order-uuid", "status": "FILLED"})
        )

        result = await get_order(order_id="order-uuid")
        assert '"order_id"' in result
        assert "order-uuid" in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_order = AsyncMock(side_effect=Exception("not found"))

        result = await get_order(order_id="bad-id")
        assert "Error" in result


class TestGetQuotes:
    async def test_returns_quotes(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_quotes = AsyncMock(
            return_value=_make_model({"quotes": [{"symbol": "AAPL", "last": "200.00"}]})
        )

        result = await get_quotes(symbols=["AAPL"])
        assert "AAPL" in result

    async def test_invalid_instrument_type_returns_error(self, patch_get_client):
        result = await get_quotes(symbols=["AAPL"], instrument_type="INVALID")
        assert "Error" in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_quotes = AsyncMock(side_effect=Exception("rate limited"))

        result = await get_quotes(symbols=["AAPL"])
        assert "Error" in result


class TestGetHistory:
    async def test_returns_history(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_history = AsyncMock(
            return_value=_make_model({"events": []})
        )

        result = await get_history()
        assert '"events"' in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_history = AsyncMock(side_effect=Exception("server error"))

        result = await get_history()
        assert "Error" in result


class TestGetInstrument:
    async def test_returns_instrument_details(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_instrument = AsyncMock(
            return_value=_make_model({"symbol": "AAPL", "tradeable": True})
        )

        result = await get_instrument(symbol="AAPL")
        assert "AAPL" in result

    async def test_invalid_instrument_type_returns_error(self, patch_get_client):
        result = await get_instrument(symbol="AAPL", instrument_type="INVALID")
        assert "Error" in result


class TestGetOptionGreeks:
    async def test_returns_greeks(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_option_greeks = AsyncMock(
            return_value=_make_model({"greeks": []})
        )

        result = await get_option_greeks(osi_symbols=["AAPL260320C00280000"])
        assert '"greeks"' in result

    async def test_api_error_returns_error_string(self, patch_get_client):
        mock_client = patch_get_client
        mock_client.get_option_greeks = AsyncMock(side_effect=Exception("bad symbol"))

        result = await get_option_greeks(osi_symbols=["INVALID"])
        assert "Error" in result
