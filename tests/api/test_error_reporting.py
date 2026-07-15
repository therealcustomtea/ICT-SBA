from __future__ import annotations

from typing import Any

import pytest
from mastermind_api.config import Settings
from mastermind_api.error_reporting import ErrorReporter


def test_error_reporting_configuration_is_paired_and_https() -> None:
    with pytest.raises(ValueError, match="configured together"):
        Settings(environment="test", error_reporting_url="https://errors.example.test/events")
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(
            environment="test",
            error_reporting_url="http://errors.example.test/events",
            error_reporting_token="token",
        )


async def test_error_report_envelope_is_allowlisted(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *, timeout: float) -> None:
            assert timeout == 2.0

        async def __aenter__(self) -> FakeClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            json: dict[str, Any],
            headers: dict[str, str],
        ) -> FakeResponse:
            sent.update(url=url, json=json, headers=headers)
            return FakeResponse()

    monkeypatch.setattr("mastermind_api.error_reporting.httpx.AsyncClient", FakeClient)
    reporter = ErrorReporter(
        Settings(
            environment="test",
            release="release-sha",
            error_reporting_url="https://errors.example.test/events",
            error_reporting_token="server-only-token",
        )
    )

    await reporter.capture(
        code="INTERNAL_ERROR",
        request_id="request-1",
        correlation_id="journey-1",
        route="/v1/games/{game_id}/attempts",
    )

    assert sent["url"] == "https://errors.example.test/events"
    assert sent["headers"] == {"Authorization": "Bearer server-only-token"}
    assert set(sent["json"]) == {
        "code",
        "requestId",
        "correlationId",
        "route",
        "environment",
        "release",
    }
