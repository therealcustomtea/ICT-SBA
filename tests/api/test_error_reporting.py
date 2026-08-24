# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import Settings

# Imports selected names from `mastermind_api.error_reporting` for use in this module.
from mastermind_api.error_reporting import ErrorReporter


# Defines the `test_error_reporting_configuration_is_paired_and_https` callable and its typed
# interface.
def test_error_reporting_configuration_is_paired_and_https() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="configured together"):
        # Calls `Settings` with the supplied values.
        Settings(environment="test", error_reporting_url="https://errors.example.test/events")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(ValueError, match="HTTPS"):
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="test",
            # Provides the `error_reporting_url` parameter or keyword argument.
            error_reporting_url="http://errors.example.test/events",
            # Provides the `error_reporting_token` parameter or keyword argument.
            error_reporting_token="token",
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `test_error_report_envelope_is_allowlisted` callable and its typed interface.
async def test_error_report_envelope_is_allowlisted(monkeypatch: pytest.MonkeyPatch) -> None:
    # Computes and stores `sent` for subsequent operations.
    sent: dict[str, Any] = {}

    # Defines the `FakeResponse` class and its related behavior.
    class FakeResponse:
        # Defines the `raise_for_status` callable and its typed interface.
        def raise_for_status(self) -> None:
            # Returns this result to the caller and ends the current function.
            return None

    # Defines the `FakeClient` class and its related behavior.
    class FakeClient:
        # Defines the `__init__` callable and its typed interface.
        def __init__(self, *, timeout: float) -> None:
            # Asserts this invariant so an unexpected test state fails immediately.
            assert timeout == 2.0

        # Defines the `__aenter__` callable and its typed interface.
        async def __aenter__(self) -> FakeClient:
            # Returns this result to the caller and ends the current function.
            return self

        # Defines the `__aexit__` callable and its typed interface.
        async def __aexit__(self, *_args: object) -> None:
            # Returns this result to the caller and ends the current function.
            return None

        # Defines the `post` callable and its typed interface.
        async def post(
            # Declares the current instance received by this method.
            self,
            # Declares the typed `url` data field.
            url: str,
            # Makes the following parameters keyword-only for clear call sites.
            *,
            # Declares the typed `json` data field.
            json: dict[str, Any],
            # Declares the typed `headers` data field.
            headers: dict[str, str],
            # Completes the signature and declares the callable return type.
        ) -> FakeResponse:
            # Calls `sent.update` with the supplied values.
            sent.update(url=url, json=json, headers=headers)
            # Returns this result to the caller and ends the current function.
            return FakeResponse()

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr("mastermind_api.error_reporting.httpx.AsyncClient", FakeClient)
    # Computes and stores `reporter` for subsequent operations.
    reporter = ErrorReporter(
        # Calls `Settings` with the supplied values.
        Settings(
            # Provides the `environment` parameter or keyword argument.
            environment="test",
            # Provides the `release` parameter or keyword argument.
            release="release-sha",
            # Provides the `error_reporting_url` parameter or keyword argument.
            error_reporting_url="https://errors.example.test/events",
            # Provides the `error_reporting_token` parameter or keyword argument.
            error_reporting_token="server-only-token",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )

    # Waits for this asynchronous operation to complete.
    await reporter.capture(
        # Provides the `code` parameter or keyword argument.
        code="INTERNAL_ERROR",
        # Provides the `request_id` parameter or keyword argument.
        request_id="request-1",
        # Provides the `correlation_id` parameter or keyword argument.
        correlation_id="journey-1",
        # Provides the `route` parameter or keyword argument.
        route="/v1/games/{game_id}/attempts",
        # Closes the multiline call, declaration, or collection started above.
    )

    # Asserts this invariant so an unexpected test state fails immediately.
    assert sent["url"] == "https://errors.example.test/events"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sent["headers"] == {"Authorization": "Bearer server-only-token"}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert set(sent["json"]) == {
        # Supplies this item to the surrounding call or collection.
        "code",
        # Supplies this item to the surrounding call or collection.
        "requestId",
        # Supplies this item to the surrounding call or collection.
        "correlationId",
        # Supplies this item to the surrounding call or collection.
        "route",
        # Supplies this item to the surrounding call or collection.
        "environment",
        # Supplies this item to the surrounding call or collection.
        "release",
        # Closes the multiline call, declaration, or collection started above.
    }
