# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports `httpx` so the module can use that dependency.
import httpx

# Imports `structlog` so the module can use that dependency.
import structlog

# Imports selected names from `.config` for use in this module.
from .config import Settings


# Defines the `ErrorReporter` class and its related behavior.
class ErrorReporter:
    # Documents the purpose or contract of this module, class, or function.
    """Minimal allowlisted error sink with no exception, identity, or request payload data."""

    # Defines the `__init__` callable and its typed interface.
    def __init__(self, settings: Settings) -> None:
        # Computes and stores `self.url` for subsequent operations.
        self.url = settings.error_reporting_url
        # Computes and stores `self.token` for subsequent operations.
        self.token = settings.error_reporting_token
        # Computes and stores `self.environment` for subsequent operations.
        self.environment = settings.environment
        # Computes and stores `self.release` for subsequent operations.
        self.release = settings.release

    # Applies `@property` to configure the declaration immediately below.
    @property
    # Defines the `enabled` callable and its typed interface.
    def enabled(self) -> bool:
        # Returns this result to the caller and ends the current function.
        return bool(self.url and self.token)

    # Defines the `capture` callable and its typed interface.
    async def capture(
        # Declares the current instance received by this method.
        self,
        # Makes the following parameters keyword-only for clear call sites.
        *,
        # Declares the typed `code` data field.
        code: str,
        # Declares the typed `request_id` data field.
        request_id: str,
        # Declares the typed `correlation_id` data field.
        correlation_id: str,
        # Declares the typed `route` data field.
        route: str,
        # Completes the signature and declares the callable return type.
    ) -> None:
        # Checks this condition before executing the nested branch.
        if not self.enabled:
            # Returns this result to the caller and ends the current function.
            return
        # Computes and stores `payload` for subsequent operations.
        payload: dict[str, Any] = {
            # Associates the `code` key with its value.
            "code": code,
            # Associates the `requestId` key with its value.
            "requestId": request_id,
            # Associates the `correlationId` key with its value.
            "correlationId": correlation_id,
            # Associates the `route` key with its value.
            "route": route,
            # Associates the `environment` key with its value.
            "environment": self.environment,
            # Associates the `release` key with its value.
            "release": self.release,
            # Closes the multiline call, declaration, or collection started above.
        }
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Acquires this asynchronous managed resource for the nested operation.
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Computes and stores `response` for subsequent operations.
                response = await client.post(
                    # Supplies this item to the surrounding call or collection.
                    self.url,
                    # Provides the `json` parameter or keyword argument.
                    json=payload,
                    # Provides the `headers` parameter or keyword argument.
                    headers={"Authorization": f"Bearer {self.token}"},
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Uses the current HTTP request or response in this operation.
                response.raise_for_status()
        # Handles the listed exception so failure remains controlled.
        except httpx.HTTPError:
            # Calls `structlog.get_logger` with the supplied values.
            structlog.get_logger().warning(
                # Supplies this item to the surrounding call or collection.
                "error_report_delivery_failed",
                # Provides the `request_id` parameter or keyword argument.
                request_id=request_id,
                # Provides the `environment` parameter or keyword argument.
                environment=self.environment,
                # Provides the `release` parameter or keyword argument.
                release=self.release,
                # Closes the multiline call, declaration, or collection started above.
            )
