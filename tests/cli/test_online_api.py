"""Exercise terminal workflows through the real FastAPI handlers and isolated MongoDB."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import uuid
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from mastermind_api.auth import get_current_user
from mastermind_api.models import AdminGrant
from mastermind_api.routers.auth import _totp
from mastermind_cli.online import OnlineCLI
from mastermind_cli.online_client import OnlineClient, OnlineError

from tests.api.conftest import APIContext

pytestmark = pytest.mark.mongodb


class HandlerTransport(httpx.BaseTransport):
    def __init__(self, api_client: httpx.AsyncClient, loop: asyncio.AbstractEventLoop) -> None:
        self.api_client, self.loop = api_client, loop

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        async def dispatch() -> httpx.Response:
            response = await self.api_client.send(request)
            return httpx.Response(
                response.status_code, headers=response.headers, content=response.content
            )

        return asyncio.run_coroutine_threadsafe(dispatch(), self.loop).result(timeout=20)


async def run_terminal(
    api: APIContext, directory: Path, callback: Callable[[OnlineClient], None]
) -> None:
    api.app.dependency_overrides.pop(get_current_user)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app, raise_app_exceptions=True)
    ) as bridge:
        transport = HandlerTransport(bridge, asyncio.get_running_loop())

        def run() -> None:
            client = OnlineClient(state_dir=directory, transport=transport)
            try:
                client.connect()
                callback(client)
            finally:
                client.close()

        await asyncio.to_thread(run)


async def test_cli_online_pass_and_play_resume_stats_and_authorization(
    api: APIContext,
    tmp_path: Path,
) -> None:
    def flow(client: OnlineClient) -> None:
        answers = iter(["3", "2", "1", "RBGY"])
        output: list[str] = []
        app = OnlineCLI(
            client,
            input_fn=lambda _prompt: next(answers),
            secret_input_fn=lambda _prompt: "RBGY",
            output_fn=output.append,
        )
        app.new_game()
        history = client.request("GET", "/v1/me/games")
        assert history["total"] == 1
        saved = history["items"][0]
        assert saved["status"] == "won" and saved["mode"] == "pass_and_play"
        assert saved["attemptsUsed"] == 1
        assert client.request("GET", "/v1/me/stats")["gamesWon"] == 1
        assert "RBGY" not in client.state.path.read_text()
        with pytest.raises(OnlineError) as error:
            client.request("GET", "/v1/admin/summary")
        assert error.value.status == 403
        client.logout()
        client.connect()
        with pytest.raises(OnlineError) as error:
            client.request("GET", f"/v1/games/{saved['id']}")
        assert error.value.status == 404

    await run_terminal(api, tmp_path, flow)


async def test_cli_daily_and_friend_challenges_use_server_rules(
    api: APIContext,
    tmp_path: Path,
) -> None:
    def flow(client: OnlineClient) -> None:
        first = client.request("POST", "/v1/daily/start", {"practice": False})
        resumed = client.request("POST", "/v1/daily/start", {"practice": False})
        assert first["id"] == resumed["id"]
        client.request("POST", f"/v1/games/{first['id']}/abandon")
        practice = client.request("POST", "/v1/daily/start", {"practice": True})
        assert practice["id"] != first["id"] and practice["ranked"] is False
        client.request("GET", "/v1/daily/leaderboard?page=1&page_size=20")
        creation_input = iter(["n", "1", "1", "CLI challenge", "n"])
        output: list[str] = []
        creator = OnlineCLI(
            client,
            input_fn=lambda _prompt: next(creation_input),
            output_fn=output.append,
        )
        creator.create_challenge()
        created = next(json.loads(line) for line in output if line.startswith("{"))
        share = created["shareCode"]
        looked_up = client.request("GET", f"/v1/challenges/{share}")
        assert looked_up["title"] == "CLI challenge"
        assert "secret" not in looked_up
        played = client.request("POST", f"/v1/challenges/{share}/start", {"practice": False})
        assert played["mode"] == "friend_challenge"
        assert played["secret"] is None
        owned = client.request("GET", "/v1/challenges/mine")
        identifier = owned["items"][0]["id"]
        client.request("GET", f"/v1/challenges/{identifier}/results")
        client.request("DELETE", f"/v1/challenges/{identifier}")
        with pytest.raises(OnlineError) as error:
            client.request("GET", f"/v1/challenges/{share}")
        assert error.value.status == 404

    await run_terminal(api, tmp_path, flow)


async def test_cli_profile_support_and_public_leaderboard_workflows(
    api: APIContext,
    tmp_path: Path,
) -> None:
    def flow(client: OnlineClient) -> None:
        client.request("GET", "/v1/me/profile")
        # Upgrade before profile mutations; guests intentionally retain restricted account controls.
        with pytest.raises(OnlineError) as denied:
            client.download("/v1/me/export", tmp_path / "guest.zip")
        assert denied.value.status == 403
        inputs = iter(["2", "terminal@example.test", "Please explain the feedback pegs.", "y"])
        output: list[str] = []
        OnlineCLI(client, input_fn=lambda _prompt: next(inputs), output_fn=output.append).support()
        assert any('"received": true' in line for line in output)
        listing = iter(["n", "0", ""])
        OnlineCLI(
            client, input_fn=lambda _prompt: next(listing), output_fn=output.append
        ).leaderboard()
        assert any('"currentUserRank"' in line for line in output)

    await run_terminal(api, tmp_path, flow)


async def test_cli_magic_link_upgrade_export_delete_and_old_session_revocation(
    api: APIContext,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    links: list[str] = []

    async def capture_email(_settings: Any, _recipient: str, link: str) -> None:
        links.append(link)

    monkeypatch.setattr("mastermind_api.routers.auth._send_email", capture_email)

    def flow(client: OnlineClient) -> None:
        guest_id = client.user["id"]
        client.request("POST", "/v1/auth/email", {"email": "terminal@example.test"})
        client.verify_email(links[-1])
        assert client.user["id"] == guest_id
        profile = client.request(
            "PATCH",
            "/v1/me/profile",
            {
                "displayName": "Terminal Player",
                "publicLeaderboards": True,
            },
        )
        assert profile["isAnonymous"] is False
        target = tmp_path / "export.zip"
        client.download("/v1/me/export", target)
        with zipfile.ZipFile(io.BytesIO(target.read_bytes())) as archive:
            assert any(name.endswith("profile.json") for name in archive.namelist())
        old_token = client.token
        result = client.request("DELETE", "/v1/me", {"confirmation": "DELETE"})
        assert result["deleted"] is True
        client.logout(remote=False)
        client.connect()
        assert client.user["id"] != guest_id
        response = client.http.get(
            "/v1/me/profile", headers={"Authorization": f"Bearer {old_token}"}
        )
        assert response.status_code == 401
        assert "accessToken" not in json.loads(client.state.path.read_text())

    await run_terminal(api, tmp_path, flow)


async def test_cli_mfa_and_admin_actions_preserve_grant_and_audit_requirements(
    api: APIContext,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    links: list[str] = []
    loop = asyncio.get_running_loop()

    async def capture_email(_settings: Any, _recipient: str, link: str) -> None:
        links.append(link)

    async def grant(user_id: str) -> None:
        async with api.sessions() as database:
            database.add(AdminGrant(user_id=uuid.UUID(user_id)))
            await database.commit()

    monkeypatch.setattr("mastermind_api.routers.auth._send_email", capture_email)

    def flow(client: OnlineClient) -> None:
        client.request("POST", "/v1/auth/email", {"email": "admin-cli@example.test"})
        client.verify_email(links[-1])
        client.request("GET", "/v1/me/profile")
        setup = client.request("POST", "/v1/auth/mfa/totp/setup")
        secret = setup["secret"]
        import time

        code = _totp(base64.b32decode(secret + "=" * (-len(secret) % 8)), int(time.time()) // 30)
        client.verify_totp(code)
        with pytest.raises(OnlineError) as denied:
            client.request("GET", "/v1/admin/summary")
        assert denied.value.status == 403
        asyncio.run_coroutine_threadsafe(grant(client.user["id"]), loop).result(timeout=10)
        summary = client.request("GET", "/v1/admin/summary")
        assert summary["profiles"] >= 1
        flags = client.request("GET", "/v1/admin/flags")
        flag = flags[0]
        client.request(
            "PATCH",
            f"/v1/admin/flags/{flag['key']}",
            {
                "enabled": flag["enabled"],
                "reason": "CLI integration verification",
            },
        )
        audit = client.request("GET", "/v1/admin/audit")
        assert any(item["reason"] == "CLI integration verification" for item in audit)
        assert secret not in client.state.path.read_text()

    await run_terminal(api, tmp_path, flow)
