from __future__ import annotations

import base64
import json
import os
import stat
from pathlib import Path
from typing import Any

import httpx
import pytest
from mastermind_cli.online import OnlineCLI, safe_text
from mastermind_cli.online_client import ClientState, OnlineClient, OnlineError, server_origin


def test_public_email_issuer_can_differ_from_the_internal_docker_api(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.host == "api"
        if request.url.path.endswith("/verify"):
            return httpx.Response(303, headers={"location": "http://127.0.0.1:3000/en/profile"})
        return httpx.Response(200, json=session())

    client = OnlineClient(
        "http://api:8000",
        allow_http=True,
        state_dir=tmp_path,
        transport=httpx.MockTransport(respond),
    )
    payload = (
        base64.urlsafe_b64encode(json.dumps({"iss": "http://127.0.0.1:8000"}).encode())
        .decode()
        .rstrip("=")
    )
    try:
        client._apply_session(session(f"header.{payload}.signature"))
        client.verify_email("http://127.0.0.1:8000/v1/auth/email/verify?token=one-use")
        assert [request.url.path for request in requests] == [
            "/v1/auth/email/verify",
            "/v1/auth/refresh",
        ]
    finally:
        client.close()


def test_resource_creation_retries_keep_the_original_idempotency_key(tmp_path: Path) -> None:
    bodies: list[dict[str, Any]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        if len(bodies) == 1:
            raise httpx.ReadTimeout("Response lost")
        return httpx.Response(201, json={"id": "same-room"})

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    client._apply_session(session())
    script = Script(["y"])
    try:
        result = OnlineCLI(
            client, input_fn=script.input, output_fn=script.output.append
        ).create_resource(
            "/v1/rooms", {"difficulty": "easy", "idempotencyKey": "original-creation-key"}
        )
        assert result["id"] == "same-room"
        assert bodies[0] == bodies[1]
    finally:
        client.close()


CONFIG = {
    "colours": ["R", "B", "G", "Y", "W", "K"],
    "codeLength": 4,
    "maxAttempts": 10,
    "duplicatesAllowed": True,
    "codeMaker": "computer",
    "visibility": "private",
    "ranked": False,
    "timeBonusCap": 300,
}


def game(*, won: bool = False) -> dict[str, Any]:
    return {
        "id": "game-one",
        "mode": "practice",
        "difficulty": "normal",
        "status": "won" if won else "active",
        "config": CONFIG,
        "attempts": [
            {"number": 1, "guess": ["R", "B", "G", "Y"], "feedback": {"black": 4, "white": 0}}
        ]
        if won
        else [],
        "attemptsUsed": int(won),
        "attemptsRemaining": 9 if won else 10,
        "maxAttempts": 10,
        "score": 1000 if won else None,
        "scoreBreakdown": None,
        "secret": ["R", "B", "G", "Y"] if won else None,
        "ranked": False,
    }


def session(access_value: str = "access-one") -> dict[str, Any]:
    return {
        "accessToken": access_value,
        "expiresIn": 3600,
        "user": {"id": "user-one", "isAnonymous": True},
    }


class Script:
    def __init__(self, answers: list[str]) -> None:
        self.answers = iter(answers)
        self.output: list[str] = []

    def input(self, _prompt: str) -> str:
        return next(self.answers)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://name:password@example.com",
        "https://example.com/path",
        "https://example.com?token=secret",
        "file:///tmp/api",
    ],
)
def test_server_origin_rejects_unsafe_credential_destinations(url: str) -> None:
    with pytest.raises(ValueError):
        server_origin(url)
    assert server_origin("https://example.com/") == "https://example.com"
    assert server_origin("http://api:8000", allow_http=True) == "http://api:8000"


def test_session_cookie_rotation_is_private_and_access_tokens_stay_in_memory(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/auth/guest":
            assert "authorization" not in request.headers
            return httpx.Response(
                201,
                json=session(),
                headers={"set-cookie": "cb_refresh=one; Path=/v1/auth; HttpOnly"},
            )
        if request.url.path == "/v1/auth/refresh":
            assert "cb_refresh=one" in request.headers["cookie"]
            return httpx.Response(
                200,
                json=session("access-two"),
                headers={"set-cookie": "cb_refresh=two; Path=/v1/auth; HttpOnly"},
            )
        assert request.headers["authorization"] == "Bearer access-two"
        return httpx.Response(200, json={"id": "user-one"})

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    try:
        client.connect()
        saved = client.state.path.read_text()
        assert "access-one" not in saved
        assert "cb_refresh" in saved
        if os.name == "posix":
            assert stat.S_IMODE(client.state.path.stat().st_mode) == 0o600
        with pytest.raises(OnlineError) as in_use:
            OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
        assert in_use.value.code == "SESSION_IN_USE"
        client.close()
        restored = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
        try:
            restored.connect()
            restored.request("GET", "/v1/me/profile")
            assert '"value": "two"' in restored.state.path.read_text()
        finally:
            restored.close()
        assert [r.url.path for r in requests] == [
            "/v1/auth/guest",
            "/v1/auth/refresh",
            "/v1/me/profile",
        ]
    finally:
        client.close()


def test_email_verification_rejects_other_origins_and_never_follows_redirect(
    tmp_path: Path,
) -> None:
    paths: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/verify"):
            assert request.url.params["token"] == "one-use"
            return httpx.Response(
                303,
                headers={
                    "location": "https://other.example/profile",
                    "set-cookie": "cb_refresh=ok; Path=/v1/auth",
                },
            )
        return httpx.Response(200, json=session())

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(OnlineError, match="this API server"):
            client.verify_email("https://attacker.example/v1/auth/email/verify?token=one-use")
        assert paths == []
        client.verify_email("http://127.0.0.1:8000/v1/auth/email/verify?token=one-use")
        assert paths == ["/v1/auth/email/verify", "/v1/auth/refresh"]
    finally:
        client.close()


def test_pending_guess_survives_a_network_failure_and_retries_with_the_same_key(
    tmp_path: Path,
) -> None:
    attempts: list[dict[str, Any]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/guest"):
            return httpx.Response(201, json=session())
        if request.url.path.endswith("/attempts"):
            attempts.append(json.loads(request.content))
            if len(attempts) == 1:
                raise httpx.ReadTimeout("sensitive URL must not reach the terminal")
            return httpx.Response(200, json=game(won=True))
        return httpx.Response(200, json={"achievements": ["first_break"]})

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    script = Script(["R B G Y", "retry"])
    try:
        client.connect()
        OnlineCLI(client, input_fn=script.input, output_fn=script.output.append).play(game())
        assert len(attempts) == 2 and attempts[0] == attempts[1]
        assert client.state.data["pending"] == {}
        assert "sensitive URL" not in "\n".join(script.output)
        assert "first_break" in "\n".join(script.output)
    finally:
        client.close()


def test_account_export_preserves_an_existing_file_unless_confirmed(tmp_path: Path) -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=b"PK-test-archive", headers={"content-type": "application/zip"}
        )

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    client._apply_session(session())
    target = tmp_path / "account.zip"
    target.write_bytes(b"original")
    try:
        with pytest.raises(FileExistsError):
            client.download("/v1/me/export", target)
        assert target.read_bytes() == b"original"
        client.download("/v1/me/export", target, overwrite=True)
        assert target.read_bytes() == b"PK-test-archive"
        assert not list(tmp_path.glob(".export-*"))
    finally:
        client.close()


def test_deletion_requires_exact_confirmation_and_server_authorization(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            403, json={"code": "ACCOUNT_UPGRADE_REQUIRED", "message": "Upgrade first."}
        )

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    client._apply_session(session())
    try:
        script = Script(["delete", "DELETE"])
        app = OnlineCLI(client, input_fn=script.input, output_fn=script.output.append)
        app.delete_account()
        assert requests == []
        with pytest.raises(OnlineError) as error:
            app.delete_account()
        assert error.value.status == 403
        assert json.loads(requests[0].content) == {"confirmation": "DELETE"}
        assert client.token is not None
    finally:
        client.close()


def test_menu_localization_pagination_and_admin_denial(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/me/profile":
            return httpx.Response(200, json={"id": "user-one"})
        if "/admin/" in request.url.path:
            return httpx.Response(403, json={"code": "ADMIN_REQUIRED", "message": "Access denied."})
        return httpx.Response(
            200, json={"items": [], "page": int(request.url.params["page"]), "total": 22}
        )

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    client._apply_session(session())
    script = Script(["n", "", "11", "0"])
    try:
        app = OnlineCLI(
            client, input_fn=script.input, output_fn=script.output.append, locale="zh-Hant"
        )
        app.browse("/v1/leaderboards", {"period": "weekly"})
        assert [r.url.params["page"] for r in requests] == ["1", "2"]
        app.run()
        assert "線上功能" in "\n".join(script.output)
        assert "ADMIN_REQUIRED" in "\n".join(script.output)
        assert requests[-1].url.path == "/v1/admin/summary"
    finally:
        client.close()


def test_malformed_private_state_and_terminal_injection_are_rejected(tmp_path: Path) -> None:
    state = ClientState("https://example.com", tmp_path)
    state.directory.mkdir(parents=True)
    state.path.write_text('{"preferences": []}')
    state.path.chmod(0o600)
    with pytest.raises(ValueError, match="invalid settings"):
        ClientState("https://example.com", tmp_path)
    assert safe_text("name\x1b[2J\u202eevil") == "name[2Jevil"


def test_preferences_affect_the_terminal_and_analytics_requires_explicit_consent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"received": True})

    client = OnlineClient(state_dir=tmp_path, transport=httpx.MockTransport(respond))
    client._apply_session(session())
    script = Script(["2", "3", "3", "n", "y"])
    try:
        app = OnlineCLI(client, input_fn=script.input, output_fn=script.output.append)
        app.event("game_started", {"mode": "solo", "difficulty": "easy"})
        assert requests == []
        app.settings()
        monkeypatch.setenv("FORCE_COLOR", "1")
        app.game_board(game(won=True))
        rendered = "\n".join(script.output)
        assert "剩餘次數" in rendered
        assert "R/0 B/1 G/2 Y/3" in rendered
        assert "\x1b" not in rendered
        app.event("game_started", {"mode": "solo", "difficulty": "easy"})
        assert len(requests) == 1
        event = json.loads(requests[0].content)
        assert event["consent"] is True and event["locale"] == "zh-Hant"
        assert "guess" not in event and "secret" not in event
    finally:
        client.close()
