"""Two terminal transports connect to the real room WebSocket implementation."""

from __future__ import annotations

import asyncio
import json
import queue
import socket
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from mastermind_api.auth import get_current_user
from mastermind_api.config import get_settings
from mastermind_api.realtime import RedisBroker
from mastermind_cli.online import OnlineCLI
from mastermind_cli.online_client import DuelConnection, OnlineClient, OnlineError
from redis.asyncio import Redis

from tests.api.conftest import APIContext

pytestmark = pytest.mark.mongodb


async def test_two_cli_clients_submit_private_duel_guesses_and_resume_durable_replay(
    api: APIContext,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_url = get_settings().redis_url
    if redis_url is None:
        pytest.skip("The live terminal room test requires Redis.")
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.ping()
    await api.app.state.broker.close()
    api.app.state.redis = redis
    api.app.state.redis_ready = True
    api.app.state.broker = RedisBroker(redis)
    api.app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr("mastermind_api.routers.rooms.get_settings", lambda: api.settings)
    monkeypatch.setattr(
        "mastermind_api.services.generate_secret", lambda config: tuple(config.colours[:4])
    )
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(api.app, log_level="error", lifespan="off"))
    serving = asyncio.create_task(server.serve(sockets=[listener]))
    for _ in range(100):
        if server.started:
            break
        await asyncio.sleep(0.02)
    assert server.started

    def acknowledged(connection: DuelConnection) -> dict[str, Any]:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                event = connection.events.get(timeout=1)
            except queue.Empty:
                continue
            if event.get("type") == "error":
                pytest.fail(json.dumps(event))
            if event.get("type") == "opponent_progress":
                assert "guess" not in event["payload"]
                assert "secret" not in event["payload"]
            if event.get("type") == "attempt_result":
                return event
        pytest.fail("No private attempt acknowledgement arrived.")

    def flow() -> None:
        first = OnlineClient(
            f"http://127.0.0.1:{port}",
            product_origin=api.settings.allowed_origins[0],
            state_dir=tmp_path / "first",
        )
        second = OnlineClient(
            f"http://127.0.0.1:{port}",
            product_origin=api.settings.allowed_origins[0],
            state_dir=tmp_path / "second",
        )
        try:
            first.connect()
            second.connect()
            created = first.request(
                "POST", "/v1/rooms", {"difficulty": "normal", "idempotencyKey": uuid.uuid4().hex}
            )
            identifier = created["id"]
            second.request("POST", f"/v1/rooms/{created['roomCode']}/join")
            first.request("POST", f"/v1/rooms/{identifier}/ready")
            second.request("POST", f"/v1/rooms/{identifier}/ready")
            room = first.request("GET", f"/v1/rooms/{identifier}")
            own_game = next(
                member["gameId"]
                for member in room["members"]
                if member["userId"] == first.user["id"]
            )
            with pytest.raises(OnlineError) as denied:
                second.request("GET", f"/v1/games/{own_game}")
            assert denied.value.status == 404
            first_message = {
                "version": 1,
                "type": "guess",
                "guess": ["R"] * 4,
                "idempotencyKey": uuid.uuid4().hex,
            }
            second_message = {
                "version": 1,
                "type": "guess",
                "guess": ["B"] * 4,
                "idempotencyKey": uuid.uuid4().hex,
            }
            with (
                DuelConnection(first, identifier) as host,
                DuelConnection(second, identifier) as guest,
            ):
                host.send(first_message)
                guest.send(second_message)
                assert acknowledged(host)["payload"]["number"] == 1
                assert acknowledged(guest)["payload"]["number"] == 1
                cursor = host.sequence
            assert not host.thread.is_alive() and not guest.thread.is_alive()
            with DuelConnection(first, identifier) as restored:
                restored.send(first_message)
                replayed = acknowledged(restored)
                assert replayed["payload"]["duplicate"] is True
                assert restored.sequence >= cursor
                assert first.request("GET", f"/v1/games/{own_game}")["attemptsUsed"] == 1
            assert not restored.thread.is_alive()
            inputs = iter(["RBG", "back"])
            output: list[str] = []
            OnlineCLI(
                first,
                input_fn=lambda _prompt: next(inputs),
                output_fn=output.append,
            ).room(first.request("GET", f"/v1/rooms/{identifier}"))
            assert first.state.data.get("pending", {}) == {}
            assert any("INVALID_GUESS_LENGTH" in line for line in output)
        finally:
            first.close()
            second.close()

    try:
        await asyncio.to_thread(flow)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "mastermind_cli",
            "--online",
            "--api-url",
            f"http://127.0.0.1:{port}",
            "--state-dir",
            str(tmp_path / "entrypoint"),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(b"0\n"), timeout=20)
        assert process.returncode == 0, stderr.decode()
        assert "Online features" in stdout.decode()
        assert "accessToken" not in stdout.decode()
    finally:
        server.should_exit = True
        await asyncio.wait_for(serving, timeout=10)
        listener.close()
