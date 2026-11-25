"""HTTP and WebSocket transports for the server-authoritative terminal client."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import queue
import stat
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import parse_qs, quote, urlsplit

import httpx
from websockets.exceptions import WebSocketException
from websockets.sync.client import ClientConnection, connect

JSON = dict[str, Any]


class OnlineError(Exception):
    """An actionable client error without credentials or raw response bodies."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def server_origin(value: str, *, allow_http: bool = False) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use an HTTP(S) server origin without credentials, path, or query.")
    if (
        parsed.scheme == "http"
        and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        and not allow_http
    ):
        raise ValueError("Remote servers require HTTPS. Use --allow-http for a trusted LAN.")
    try:
        return str(httpx.URL(value)).rstrip("/")
    except httpx.InvalidURL as exc:
        raise ValueError("Use a valid HTTP(S) server origin.") from exc


class ClientState:
    """Keep each server's refresh cookie and preferences in a private local file."""

    def __init__(self, origin: str, directory: Path | None = None) -> None:
        root = directory or Path.home() / ".config" / "cipherboard" / "cli"
        self.directory = root / hashlib.sha256(origin.encode()).hexdigest()[:24]
        self.path = self.directory / "state.json"
        self.lock = threading.RLock()
        self.data: JSON = {}
        self.session_handle: BinaryIO | None = None
        self.load()

    def load(self) -> None:
        if self.path.exists() or self.path.is_symlink():
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(self.path, flags)
            with os.fdopen(descriptor, encoding="utf-8") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 1_048_576:
                    raise ValueError("The CLI session file is invalid.")
                if os.name == "posix" and info.st_mode & 0o077:
                    raise ValueError("The CLI session file must be private (chmod 600).")
                value = json.load(handle)
                if not isinstance(value, dict):
                    raise ValueError("The CLI session file is invalid.")
                for key in ("preferences", "pending", "rooms"):
                    if key in value and not isinstance(value[key], dict):
                        raise ValueError("The CLI session file contains invalid settings.")
                self.data = value

    def prepare_directory(self) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink():
            raise ValueError("The CLI state directory cannot be a symbolic link.")
        self.directory.chmod(0o700)

    def acquire_session(self) -> None:
        """Prevent separate CLI processes from reusing a rotating refresh token."""
        self.prepare_directory()
        descriptor = os.open(
            self.directory / ".session-lock",
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        handle = os.fdopen(descriptor, "r+b")
        try:
            if sys.platform == "win32":
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise OnlineError(
                "SESSION_IN_USE", "This session is open in another CLI. Choose another --state-dir."
            ) from exc
        self.session_handle = handle
        try:
            self.load()
        except (OSError, ValueError):
            self.release_session()
            raise

    def release_session(self) -> None:
        if self.session_handle is not None:
            self.session_handle.close()
            self.session_handle = None

    def save(self) -> None:
        with self.lock:
            self.prepare_directory()
            descriptor, temporary = tempfile.mkstemp(dir=self.directory, prefix=".state-")
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump(self.data, handle, ensure_ascii=False)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
            finally:
                Path(temporary).unlink(missing_ok=True)

    def preference(self, name: str, default: Any) -> Any:
        preferences = self.data.get("preferences", {})
        return preferences.get(name, default) if isinstance(preferences, dict) else default

    def set_preference(self, name: str, value: str | bool) -> None:
        with self.lock:
            self.data.setdefault("preferences", {})[name] = value
            self.save()


class OnlineClient:
    def __init__(
        self,
        origin: str = "http://127.0.0.1:8000",
        *,
        product_origin: str = "http://127.0.0.1:3000",
        state_dir: Path | None = None,
        allow_http: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.origin = server_origin(origin, allow_http=allow_http)
        self.allow_http = allow_http
        self.auth_origin = self.origin
        self.product_origin = server_origin(product_origin, allow_http=allow_http)
        self.state = ClientState(self.origin, state_dir)
        self.state.acquire_session()
        try:
            self.http = httpx.Client(
                base_url=self.origin,
                timeout=15,
                follow_redirects=False,
                transport=transport,
                headers={"Accept": "application/json", "User-Agent": "Cipherboard-CLI/1.1"},
            )
        except BaseException:
            self.state.release_session()
            raise
        self.token: str | None = None
        self.expires_at = 0.0
        self.user: JSON = {}
        self.auth_lock = threading.RLock()
        cookies = self.state.data.get("cookies", [])
        if isinstance(cookies, list):
            for cookie in cookies:
                if not isinstance(cookie, dict) or cookie.get("path") != "/v1/auth":
                    continue
                name, value = cookie.get("name"), cookie.get("value")
                if isinstance(name, str) and isinstance(value, str):
                    self.http.cookies.set(
                        name, value, domain=httpx.URL(self.origin).host, path="/v1/auth"
                    )

    def close(self) -> None:
        try:
            self.http.close()
        finally:
            self.state.release_session()

    def _save_cookies(self) -> None:
        with self.state.lock:
            self.state.data["cookies"] = [
                {"name": cookie.name, "value": cookie.value, "path": cookie.path}
                for cookie in self.http.cookies.jar
                if cookie.path == "/v1/auth" and not cookie.is_expired()
            ]
            self.state.save()

    def _apply_session(self, value: JSON) -> None:
        if not isinstance(value, dict):
            raise OnlineError("INVALID_RESPONSE", "The server returned an invalid session.")
        token, lifetime, user = value.get("accessToken"), value.get("expiresIn"), value.get("user")
        if (
            not isinstance(token, str)
            or not token
            or not isinstance(lifetime, int)
            or lifetime <= 0
            or not isinstance(user, dict)
            or not isinstance(user.get("id"), str)
        ):
            raise OnlineError("INVALID_RESPONSE", "The server returned an invalid session.")
        with self.state.lock:
            if self.state.data.get("userId") != user["id"]:
                self.state.data.pop("pending", None)
                self.state.data.pop("rooms", None)
            self.state.data["userId"] = user["id"]
        self.token, self.user = token, user
        # Use issuer metadata from this API's session only to recognize its public email links.
        # Requests and credentials stay at self.origin; redirects are never followed.
        self.auth_origin = self.origin
        with suppress(ValueError, UnicodeError, IndexError, httpx.InvalidURL):
            encoded = token.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if isinstance(claims, dict) and isinstance(claims.get("iss"), str):
                self.auth_origin = server_origin(claims["iss"], allow_http=self.allow_http)
        self.expires_at = time.monotonic() + lifetime
        self._save_cookies()

    def connect(self) -> None:
        with self.auth_lock:
            if self.http.cookies:
                try:
                    self.refresh()
                    return
                except OnlineError as exc:
                    if exc.status != 401:
                        raise
                    self.http.cookies.clear()
            self._apply_session(self.request("POST", "/v1/auth/guest", authenticated=False))

    def refresh(self) -> None:
        with self.auth_lock:
            self._apply_session(self.request("POST", "/v1/auth/refresh", authenticated=False))

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.is_success:
            return
        code, message = "REQUEST_FAILED", "The server could not complete the request."
        with suppress(ValueError):
            error = response.json()
            if isinstance(error, dict):
                if isinstance(error.get("code"), str):
                    code = error["code"]
                if isinstance(error.get("message"), str):
                    message = error["message"][:600]
        if response.status_code == 422 and code == "REQUEST_FAILED":
            message = "Check the supplied values and try again."
        raise OnlineError(code, message, response.status_code)

    def _send(
        self, method: str, path: str, payload: JSON | None, *, authenticated: bool
    ) -> httpx.Response:
        if not path.startswith(("/v1/", "/health/")) or urlsplit(path).netloc:
            raise ValueError("Requests must use a relative Cipherboard API path.")
        with self.auth_lock:
            if authenticated and (not self.token or time.monotonic() >= self.expires_at - 30):
                self.refresh()
            headers = {"Authorization": f"Bearer {self.token}"} if authenticated else {}
            try:
                response = self.http.request(method, path, json=payload, headers=headers)
            except httpx.TransportError as exc:
                raise OnlineError(
                    "NETWORK_UNAVAILABLE", "Cannot reach the API. Check the server and connection."
                ) from exc
            if authenticated and response.status_code == 401:
                with suppress(ValueError):
                    body = response.json()
                    if isinstance(body, dict) and body.get("code") in {
                        "INVALID_ACCESS_TOKEN",
                        "SESSION_EXPIRED",
                        "TOKEN_EXPIRED",
                    }:
                        self.refresh()
                        try:
                            response = self.http.request(
                                method,
                                path,
                                json=payload,
                                headers={"Authorization": f"Bearer {self.token}"},
                            )
                        except httpx.TransportError as exc:
                            raise OnlineError(
                                "NETWORK_UNAVAILABLE", "Cannot reach the API."
                            ) from exc
            return response

    def request(
        self, method: str, path: str, payload: JSON | None = None, *, authenticated: bool = True
    ) -> Any:
        response = self._send(method, path, payload, authenticated=authenticated)
        self._check(response)
        if response.status_code == 204:
            return None
        try:
            result = response.json()
        except ValueError as exc:
            raise OnlineError("INVALID_RESPONSE", "The server returned invalid JSON.") from exc
        if not isinstance(result, dict | list):
            raise OnlineError("INVALID_RESPONSE", "The server returned an invalid response.")
        return result

    def verify_email(self, link: str) -> None:
        parsed = urlsplit(link.strip())
        accepted = {
            (parsed_origin.scheme, parsed_origin.netloc)
            for parsed_origin in (urlsplit(self.origin), urlsplit(self.auth_origin))
        }
        tokens = parse_qs(parsed.query).get("token", [])
        if (
            (parsed.scheme, parsed.netloc) not in accepted
            or parsed.path != "/v1/auth/email/verify"
            or len(tokens) != 1
            or not tokens[0]
            or len(tokens[0]) > 512
            or parsed.fragment
        ):
            raise OnlineError("INVALID_LINK", "Paste the sign-in link for this API server.")
        try:
            response = self.http.get(
                "/v1/auth/email/verify", params={"token": tokens[0], "next": "/en/profile"}
            )
        except httpx.TransportError as exc:
            raise OnlineError("NETWORK_UNAVAILABLE", "Cannot verify the sign-in link.") from exc
        if response.status_code != 303 or "invalid_callback" in response.headers.get(
            "location", ""
        ):
            raise OnlineError("INVALID_LINK", "The sign-in link is invalid or expired.")
        self.refresh()

    def verify_totp(self, code: str) -> None:
        result = self.request("POST", "/v1/auth/mfa/totp/verify", {"code": code})
        if not isinstance(result, dict):
            raise OnlineError("INVALID_RESPONSE", "The server returned an invalid MFA session.")
        token, lifetime = result.get("accessToken"), result.get("expiresIn")
        if not isinstance(token, str) or not isinstance(lifetime, int) or lifetime <= 0:
            raise OnlineError("INVALID_RESPONSE", "The server returned an invalid MFA session.")
        self.token = token
        self.expires_at = time.monotonic() + lifetime
        self.user["mfaEnabled"] = True

    def logout(self, *, remote: bool = True) -> None:
        try:
            if remote:
                self.request("POST", "/v1/auth/logout", authenticated=False)
        finally:
            self.http.cookies.clear()
            self.token, self.user, self.expires_at = None, {}, 0.0
            for name in ("cookies", "userId", "pending", "rooms"):
                self.state.data.pop(name, None)
            self.state.save()

    def download(self, path: str, destination: Path, *, overwrite: bool = False) -> None:
        response = self._send("GET", path, None, authenticated=True)
        self._check(response)
        if response.headers.get("content-type", "").split(";")[0] != "application/zip":
            raise OnlineError("INVALID_RESPONSE", "The server did not return an export archive.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".export-")
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(response.content)
                handle.flush()
                os.fsync(handle.fileno())
            if overwrite:
                os.replace(temporary, destination)
            else:
                os.link(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)


class DuelConnection:
    """Maintain heartbeats and replay while terminal input waits on the main thread."""

    def __init__(
        self,
        client: OnlineClient,
        room_id: str,
        *,
        connector: Callable[..., ClientConnection] = connect,
        on_event: Callable[[JSON], None] | None = None,
    ) -> None:
        self.client, self.room_id, self.connector = client, room_id, connector
        self.on_event = on_event
        self.events: queue.Queue[JSON] = queue.Queue(maxsize=256)
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.socket: ClientConnection | None = None
        self.send_lock = threading.Lock()
        self.thread = threading.Thread(target=self._receive, daemon=True)
        rooms = client.state.data.get("rooms", {})
        self.sequence = int(rooms.get(room_id, 0)) if isinstance(rooms, dict) else 0

    def __enter__(self) -> DuelConnection:
        self.thread.start()
        if not self.ready.wait(20):
            self.close()
            raise OnlineError("REALTIME_UNAVAILABLE", "The room connection timed out.")
        if self.socket is None:
            self.close()
            raise OnlineError("REALTIME_UNAVAILABLE", "Could not connect to the room.")
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self.stop.set()
        with suppress(WebSocketException, OSError):
            if self.socket is not None:
                self.socket.close()
        if self.thread.is_alive():
            self.thread.join(timeout=22)

    def _emit(self, event: JSON) -> None:
        if self.on_event is not None and event.get("type") in {
            "presence",
            "opponent_progress",
            "room_completed",
            "connection",
        }:
            self.on_event(event)
        try:
            self.events.put_nowait(event)
        except queue.Full:
            self.stop.set()

    def send(self, message: JSON) -> None:
        with self.send_lock:
            if self.socket is None:
                raise OnlineError("RECONNECTING", "The room is reconnecting; retry shortly.")
            try:
                self.socket.send(json.dumps(message))
            except (WebSocketException, OSError) as exc:
                raise OnlineError(
                    "RECONNECTING", "The room is reconnecting; retry shortly."
                ) from exc

    def _receive(self) -> None:
        failures = 0
        while not self.stop.is_set() and failures < 4:
            try:
                room = quote(self.room_id, safe="")
                ticket = self.client.request("POST", f"/v1/rooms/{room}/ws-ticket")["ticket"]
                url = self.client.origin.replace("https://", "wss://", 1).replace(
                    "http://", "ws://", 1
                )
                socket = self.connector(
                    f"{url}/v1/rooms/{room}/events?after={self.sequence}",
                    origin=self.client.product_origin,
                    subprotocols=["cipherboard-v1", f"ticket.{ticket}"],
                    open_timeout=5,
                    close_timeout=2,
                    max_size=65_536,
                )
                with socket:
                    self.socket = socket
                    self.ready.set()
                    last_heartbeat = time.monotonic()
                    while not self.stop.is_set():
                        if time.monotonic() - last_heartbeat >= 10:
                            self.send({"version": 1, "type": "heartbeat"})
                            last_heartbeat = time.monotonic()
                        try:
                            raw = socket.recv(timeout=1)
                        except TimeoutError:
                            continue
                        event = json.loads(raw)
                        if not isinstance(event, dict) or event.get("version") != 1:
                            raise ValueError("Invalid room event")
                        if event.get("type") == "snapshot":
                            failures = 0
                        sequence = event.get("sequence")
                        if isinstance(sequence, int):
                            self.sequence = max(self.sequence, sequence)
                            with self.client.state.lock:
                                self.client.state.data.setdefault("rooms", {})[self.room_id] = (
                                    self.sequence
                                )
                                self.client.state.save()
                        if event.get("type") != "heartbeat_ack":
                            self._emit(event)
            except (WebSocketException, OSError, OnlineError, ValueError, KeyError):
                if not self.stop.is_set():
                    failures += 1
                    self._emit({"type": "connection", "payload": {"status": "reconnecting"}})
                    self.stop.wait(min(failures, 3))
            finally:
                self.socket = None
        self.ready.set()
        if not self.stop.is_set():
            self._emit({"type": "connection", "payload": {"status": "disconnected"}})
