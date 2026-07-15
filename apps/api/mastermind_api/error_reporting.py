from __future__ import annotations

from typing import Any

import httpx
import structlog

from .config import Settings


class ErrorReporter:
    """Minimal allowlisted error sink with no exception, identity, or request payload data."""

    def __init__(self, settings: Settings) -> None:
        self.url = settings.error_reporting_url
        self.token = settings.error_reporting_token
        self.environment = settings.environment
        self.release = settings.release

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.token)

    async def capture(
        self,
        *,
        code: str,
        request_id: str,
        correlation_id: str,
        route: str,
    ) -> None:
        if not self.enabled:
            return
        payload: dict[str, Any] = {
            "code": code,
            "requestId": request_id,
            "correlationId": correlation_id,
            "route": route,
            "environment": self.environment,
            "release": self.release,
        }
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.token}"},
                )
                response.raise_for_status()
        except httpx.HTTPError:
            structlog.get_logger().warning(
                "error_report_delivery_failed",
                request_id=request_id,
                environment=self.environment,
                release=self.release,
            )
