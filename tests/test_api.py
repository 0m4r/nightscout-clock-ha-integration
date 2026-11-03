"""Tests for the NSClock HTTP API client."""

from unittest.mock import AsyncMock, patch

from custom_components.nsclock.api import NightscoutClockApiClient


async def test_report_glucose_entries_uses_api_source_endpoint() -> None:
    client = NightscoutClockApiClient("nsclock.local")
    entries = [
        {
            "dateString": "2026-10-19T14:39:00.000Z",
            "sgv": 118,
            "date": 1_792_420_740_000,
        }
    ]

    with patch.object(
        client,
        "_request",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as request:
        await client.report_glucose_entries(entries)

    request.assert_awaited_once_with("POST", "/api/v1/entries", entries)
