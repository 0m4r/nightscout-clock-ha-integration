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


async def test_set_face_uses_face_endpoint() -> None:
    client = NightscoutClockApiClient("nsclock.local")

    with patch.object(
        client,
        "_request",
        new_callable=AsyncMock,
        return_value={"status": "ok", "face": "big_text"},
    ) as request:
        await client.set_face("big_text")

    request.assert_awaited_once_with("POST", "/api/face", {"face": "big_text"})


async def test_new_firmware_and_display_endpoints() -> None:
    client = NightscoutClockApiClient("nsclock.local")
    with patch.object(
        client, "_request", new_callable=AsyncMock, return_value="revision"
    ) as request:
        assert await client.get_revision() == "revision"
    request.assert_awaited_once_with("GET", "/revision.txt")

    calls = [
        (client.get_faces, "GET", "/api/faces", None),
        (client.next_face, "POST", "/api/face/next", {}),
        (client.previous_face, "POST", "/api/face/prev", {}),
        (client.next_brightness, "POST", "/api/brightness/next", {}),
        (client.previous_brightness, "POST", "/api/brightness/prev", {}),
        (client.get_brightness, "GET", "/api/brightness", None),
        (client.scan_wifi, "GET", "/api/wifi/scan", None),
    ]
    for method, http_method, path, body in calls:
        with patch.object(client, "_request", new_callable=AsyncMock) as request:
            await method()
        if body is not None:
            request.assert_awaited_once_with(http_method, path, body)
        else:
            request.assert_awaited_once_with(http_method, path)

    with patch.object(client, "_request", new_callable=AsyncMock) as request:
        await client.set_brightness(101)
    request.assert_awaited_once_with("POST", "/api/brightness", {"value": 101})
