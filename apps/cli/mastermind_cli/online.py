"""Interactive terminal workflows backed by the same API as the web application."""
# ruff: noqa: RUF001 -- Traditional Chinese UI uses full-width punctuation.

from __future__ import annotations

import json
import queue
import time
import unicodedata
import uuid
from collections.abc import Callable
from contextlib import suppress
from dataclasses import replace
from getpass import getpass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from mastermind_core import CodeMakerType, DomainError, GameConfig, GameVisibility, get_preset
from mastermind_core.validation import normalize_code

from .app import MastermindCLI
from .online_client import JSON, DuelConnection, OnlineClient, OnlineError
from .terminal import format_code, supports_colour

Action = tuple[str, str, Callable[[], None]]


class PageText(HTMLParser):
    """Extract published policy copy without rendering scripts or navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.main = False
        self.skipped = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            self.main = True
        if tag in {"script", "style"}:
            self.skipped += 1
        if self.main and not self.skipped and tag in {"p", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.main = False
        if tag in {"script", "style"}:
            self.skipped = max(0, self.skipped - 1)

    def handle_data(self, data: str) -> None:
        if self.main and not self.skipped:
            self.parts.append(data)


def safe_text(value: str) -> str:
    """Never let server-controlled labels inject terminal escape sequences."""
    return "".join(
        character
        for character in value
        if character in "\n\t" or unicodedata.category(character) not in {"Cc", "Cf"}
    )


class OnlineCLI:
    def __init__(
        self,
        client: OnlineClient,
        *,
        input_fn: Callable[[str], str] = input,
        secret_input_fn: Callable[[str], str] = getpass,
        output_fn: Callable[[str], None] = print,
        locale: str | None = None,
    ) -> None:
        self.client = client
        self.input, self.secret_input, self.output = input_fn, secret_input_fn, output_fn
        if locale is not None:
            client.state.set_preference("locale", locale)

    def text(self, english: str, chinese: str) -> str:
        return chinese if self.client.state.preference("locale", "en") == "zh-Hant" else english

    def say(self, english: str, chinese: str | None = None) -> None:
        self.output(safe_text(self.text(english, chinese or english)))

    def ask(self, english: str, chinese: str, *, hidden: bool = False) -> str:
        read = self.secret_input if hidden else self.input
        return read(self.text(english, chinese)).strip()

    def show(self, value: Any) -> None:
        self.say(json.dumps(value, ensure_ascii=False, indent=2))

    def event(self, name: str, fields: JSON) -> None:
        if self.client.state.preference("analytics", False) is not True:
            return
        with suppress(OnlineError):
            self.client.request(
                "POST",
                "/v1/analytics/events",
                {
                    "clientEventId": str(uuid.uuid4()),
                    "eventName": name,
                    "consent": True,
                    "consentVersion": "privacy-v1",
                    "locale": self.client.state.preference("locale", "en"),
                    **fields,
                },
            )

    def yes(self, english: str, chinese: str) -> bool:
        while True:
            value = self.ask(english + " [y/n]: ", chinese + " [y/n]: ").casefold()
            if value in {"y", "yes", "是"}:
                return True
            if value in {"n", "no", "否"}:
                return False
            self.say("Enter y or n.", "請輸入 y 或 n。")

    def number(self, english: str, chinese: str, minimum: int, maximum: int) -> int:
        while True:
            value = self.ask(english, chinese)
            if value.isascii() and value.isdigit() and minimum <= int(value) <= maximum:
                return int(value)
            self.say(f"Enter {minimum} to {maximum}.", f"請輸入 {minimum} 至 {maximum}。")

    def menu(self, title: str, chinese: str, actions: list[Action]) -> None:
        while True:
            self.say("\n" + title, "\n" + chinese)
            for index, (label, translated, _) in enumerate(actions, 1):
                self.say(f"{index}. {label}", f"{index}. {translated}")
            self.say("0. Back / exit", "0. 返回／離開")
            choice = self.number("Choose: ", "選擇：", 0, len(actions))
            if choice == 0:
                return
            try:
                actions[choice - 1][2]()
            except OnlineError as exc:
                self.say(f"{exc.code}: {exc}")
            except DomainError as exc:
                self.say(f"{exc.code}: {exc.message}")
            except (OSError, ValueError, KeyError, TypeError):
                self.say(
                    "Check the input, local file permissions, and server response, then retry.",
                    "請檢查輸入、本機檔案權限及伺服器回應，然後重試。",
                )

    def run(self) -> int:
        if not self.client.token:
            self.client.connect()
        self.client.request("GET", "/v1/me/profile")
        self.say(f"Cipherboard CLI — {self.client.origin}")
        self.say(
            "Online outcomes use the same account and rules as the GUI.",
            "線上結果使用與圖形介面相同的帳戶及規則。",
        )
        self.menu(
            "Online features",
            "線上功能",
            [
                (
                    "Play / practice / custom / pass-and-play",
                    "遊戲／練習／自訂／輪流遊玩",
                    self.new_game,
                ),
                ("Resume game / account history", "繼續遊戲／帳戶紀錄", self.history),
                ("Daily challenge", "每日挑戰", self.daily),
                ("Friend challenges", "好友挑戰", self.challenges),
                ("Live private duels", "即時私人對戰", self.rooms),
                ("Profile / statistics / achievements", "個人檔案／統計／成就", self.profile),
                ("Public leaderboards", "公開排行榜", self.leaderboard),
                ("Sign-in / MFA / account controls", "登入／雙重認證／帳戶控制", self.account),
                ("Language / appearance / accessibility", "語言／外觀／無障礙設定", self.settings),
                ("Support", "支援", self.support),
                ("Administration", "管理", self.admin),
                ("Rules and privacy", "規則及私隱", self.guide),
                ("Local offline game and CSV scores", "本機離線遊戲及 CSV 分數", self.local),
            ],
        )
        return 0

    def local(self) -> None:
        MastermindCLI(
            input_fn=self.input,
            secret_input_fn=self.secret_input,
            output_fn=self.output,
            locale=self.client.state.preference("locale", "en"),
            theme=self.client.state.preference("theme", "system"),
            peg_style=self.client.state.preference("pegStyle", "symbols"),
            sound=self.client.state.preference("sound", False),
        ).run()

    def difficulty(self, *, custom: bool = True) -> tuple[str | None, GameConfig]:
        self.say(
            "1 Easy  2 Normal  3 Hard  4 Expert" + ("  5 Custom" if custom else ""),
            "1 容易  2 普通  3 困難  4 專家" + ("  5 自訂" if custom else ""),
        )
        index = self.number("Difficulty: ", "難度：", 1, 5 if custom else 4)
        if index < 5:
            name = ("easy", "normal", "hard", "expert")[index - 1]
            return name, get_preset(name)
        from mastermind_core import COLOUR_IDS

        colours = self.number("Number of colours (5-10): ", "顏色數目 (5-10)：", 5, 10)
        length = self.number("Code length (3-6): ", "密碼長度 (3-6)：", 3, 6)
        attempts = self.number("Attempts (1-20): ", "嘗試次數 (1-20)：", 1, 20)
        duplicates = self.yes("Allow duplicates?", "允許重複顏色？")
        return None, GameConfig(
            colours=COLOUR_IDS[:colours],
            code_length=length,
            max_attempts=attempts,
            duplicates_allowed=duplicates,
        )

    def selection(self, *, human: bool = False) -> JSON:
        difficulty, config = self.difficulty()
        visibility = (GameVisibility.PRIVATE, GameVisibility.SHAREABLE, GameVisibility.PUBLIC)[
            self.number(
                "Visibility: 1 Private  2 Shareable  3 Public: ",
                "可見度：1 私人  2 可分享  3 公開：",
                1,
                3,
            )
            - 1
        ]
        if human:
            config = replace(
                config, code_maker=CodeMakerType.HUMAN, visibility=visibility, ranked=False
            )
        else:
            config = replace(config, visibility=visibility)
        body: JSON = (
            {"difficulty": difficulty}
            if difficulty and not human and visibility is GameVisibility.PRIVATE
            else {"config": config.to_dict()}
        )
        if human:
            from mastermind_core import validate_code

            secret = validate_code(
                self.ask("Secret (hidden): ", "秘密密碼（隱藏輸入）：", hidden=True), config
            )
            body["secret"] = list(secret)
            self.say(
                "\n" * 40 + "Pass the terminal to the Code Breaker.",
                "\n" * 40 + "請將終端機交給猜密碼的玩家。",
            )
        return body

    def new_game(self) -> None:
        mode = self.number(
            "1 Solo  2 Practice  3 Pass-and-play: ", "1 單人  2 練習  3 輪流遊玩：", 1, 3
        )
        body = self.selection(human=mode == 3)
        body.update(
            mode=("solo", "practice", "pass_and_play")[mode - 1], idempotencyKey=uuid.uuid4().hex
        )
        game = self.create_resource("/v1/games", body)
        self.event(
            "game_started", {"mode": game["mode"], "difficulty": game.get("difficulty") or "custom"}
        )
        self.play(game)

    def create_resource(self, path: str, body: JSON) -> JSON:
        """Keep a creation key stable when a response is lost or the service is unavailable."""
        while True:
            try:
                value = self.client.request("POST", path, body)
                if not isinstance(value, dict):
                    raise OnlineError(
                        "INVALID_RESPONSE", "The server returned an invalid resource."
                    )
                return value
            except OnlineError as exc:
                if exc.status and exc.status < 500 and exc.status not in {408, 429}:
                    raise
                self.say(f"{exc.code}: {exc}")
                if not self.yes("Retry the same creation request?", "重試同一項建立請求？"):
                    raise

    def game_board(self, game: JSON) -> None:
        self.say(f"\n{game['id']} | {game['mode']} | {game['status']}")
        self.say(
            "Attempt  Guess                 Black  White",
            "次數     猜測                  黑釘   白釘",
        )
        colour = supports_colour() and self.client.state.preference("theme", "system") != "plain"
        theme = self.client.state.preference("theme", "system")
        peg_style = self.client.state.preference("pegStyle", "symbols")
        if peg_style == "highContrast":
            colour = False
        for attempt in game["attempts"]:
            guess = list(map(str, attempt["guess"]))
            rendered = format_code(guess, enabled=colour, theme=theme, peg_style=peg_style)
            plain = format_code(guess, enabled=False, theme=theme, peg_style=peg_style)
            padding = " " * max(0, 24 - len(plain))
            self.output(
                f"{attempt['number']:>7}  {rendered}{padding} "
                f"{attempt['feedback']['black']:>5} {attempt['feedback']['white']:>5}"
            )
        self.say(
            f"Attempts remaining: {game['attemptsRemaining']}",
            f"剩餘次數：{game['attemptsRemaining']}",
        )
        self.say(
            "Palette: " + " ".join(game["config"]["colours"]),
            "可用顏色：" + " ".join(game["config"]["colours"]),
        )
        if game["status"] not in {"active", "created"}:
            self.show(
                {
                    key: game.get(key)
                    for key in ("status", "score", "scoreBreakdown", "secret", "ranked")
                }
            )
            self.say(
                f"Share result: Cipherboard {game['mode']} — {game['status']}, "
                f"{game['attemptsUsed']}/{game['maxAttempts']} attempts; "
                f"score {game.get('score') or 0}.",
                f"分享結果：Cipherboard {game['mode']} — {game['status']}，"
                f"{game['attemptsUsed']}/{game['maxAttempts']} 次；分數 {game.get('score') or 0}。",
            )

    def pending(self, game_id: str) -> JSON | None:
        pending = self.client.state.data.get("pending", {}).get(game_id)
        return pending if isinstance(pending, dict) else None

    def save_pending(self, game_id: str, body: JSON | None) -> None:
        with self.client.state.lock:
            pending = self.client.state.data.setdefault("pending", {})
            if body is None:
                pending.pop(game_id, None)
            else:
                pending[game_id] = body
            self.client.state.save()

    def play(self, game: JSON) -> None:
        game_id = quote(str(game["id"]), safe="")
        while True:
            self.game_board(game)
            pending = self.pending(game_id)
            if game["status"] not in {"active", "created"} and pending is None:
                stats = self.client.request("GET", "/v1/me/stats")
                self.show({"achievements": stats.get("achievements", [])})
                return
            if pending is not None:
                self.say(
                    "An unacknowledged guess is saved. Retry uses its original key.",
                    "已儲存尚未確認的猜測，重試會使用原本的識別碼。",
                )
            raw = self.ask(
                "Guess / retry / refresh / back / abandon: ",
                "猜測／retry 重試／refresh 更新／back 返回／abandon 放棄：",
            )
            command = raw.casefold()
            if command in {"back", "quit"}:
                return
            if command == "refresh":
                game = self.client.request("GET", f"/v1/games/{game_id}")
                continue
            if command == "abandon":
                if self.yes("Abandon this game?", "放棄這局遊戲？"):
                    game = self.client.request("POST", f"/v1/games/{game_id}/abandon")
                    self.save_pending(game_id, None)
                continue
            if pending is not None and command != "retry":
                self.say(
                    "Retry or refresh the saved guess before entering another.",
                    "請先重試或更新已儲存的猜測。",
                )
                continue
            try:
                if pending is None:
                    pending = {
                        "guess": list(normalize_code(raw)),
                        "idempotencyKey": uuid.uuid4().hex,
                    }
                    self.save_pending(game_id, pending)
                game = self.client.request("POST", f"/v1/games/{game_id}/attempts", pending)
                self.save_pending(game_id, None)
                if game["status"] in {"won", "lost"}:
                    score = game.get("score") or 0
                    self.event(
                        "game_completed",
                        {
                            "mode": game["mode"],
                            "result": game["status"],
                            "attemptsUsed": game["attemptsUsed"],
                            "ranked": game["ranked"],
                            "scoreBand": "zero"
                            if score == 0
                            else "1-999"
                            if score < 1000
                            else "1000-1499"
                            if score < 1500
                            else "1500+",
                        },
                    )
                if self.client.state.preference("sound", False):
                    self.output("\a")
            except DomainError as exc:
                self.say(exc.message)
            except OnlineError as exc:
                if 400 <= exc.status < 500 and exc.status not in {401, 408, 429}:
                    self.save_pending(game_id, None)
                self.say(f"{exc.code}: {exc}")

    def browse(self, path: str, filters: JSON | None = None) -> None:
        page = 1
        while True:
            query = {**(filters or {}), "page": page, "page_size": 20}
            result = self.client.request("GET", path + "?" + urlencode(query))
            self.show(result)
            if not isinstance(result, dict) or "total" not in result:
                return
            command = self.ask(
                "n Next / p Previous / Enter Back: ", "n 下一頁／p 上一頁／Enter 返回："
            ).casefold()
            if command == "n" and page * 20 < result["total"]:
                page += 1
            elif command == "p" and page > 1:
                page -= 1
            else:
                return

    def history(self) -> None:
        self.browse("/v1/me/games")
        identifier = self.ask(
            "Game ID to resume (blank to return): ", "繼續遊戲的 ID（留空返回）："
        )
        if identifier:
            game = self.client.request("GET", f"/v1/games/{quote(identifier, safe='')}")
            if game["mode"] == "duel":
                self.say(
                    "Resume duels through Live private duels using the room ID.",
                    "請在即時私人對戰中輸入房間 ID 繼續。",
                )
                return
            self.play(game)

    def daily(self) -> None:
        self.show(self.client.request("GET", "/v1/daily"))
        self.menu(
            "Daily challenge",
            "每日挑戰",
            [
                (
                    "Start / resume official run",
                    "開始／繼續正式挑戰",
                    lambda: self.start_daily(practice=False),
                ),
                (
                    "Unranked practice",
                    "不排名練習",
                    lambda: self.start_daily(practice=True),
                ),
                ("Daily leaderboard", "每日排行榜", lambda: self.browse("/v1/daily/leaderboard")),
            ],
        )

    def start_daily(self, *, practice: bool) -> None:
        game = self.client.request("POST", "/v1/daily/start", {"practice": practice})
        if practice and game.get("ranked"):
            self.say(
                "Your active official run is resumed before practice is available.",
                "伺服器會先繼續進行中的正式挑戰，完成後才可練習。",
            )
        self.play(game)

    def challenges(self) -> None:
        self.menu(
            "Friend challenges",
            "好友挑戰",
            [
                ("Create challenge", "建立挑戰", self.create_challenge),
                ("Play shared challenge", "遊玩分享的挑戰", self.join_challenge),
                ("My challenges", "我的挑戰", lambda: self.browse("/v1/challenges/mine")),
                ("Creator results", "建立者查看結果", self.challenge_results),
                ("Revoke challenge", "撤銷挑戰", self.revoke_challenge),
            ],
        )

    def create_challenge(self) -> None:
        body = self.selection(human=self.yes("Set a human secret?", "由玩家設定秘密密碼？"))
        body["title"] = self.ask("Title (optional): ", "標題（可留空）：") or None
        body["showCreatorName"] = self.yes("Show creator name?", "顯示建立者名稱？")
        body["idempotencyKey"] = uuid.uuid4().hex
        result = self.create_resource("/v1/challenges", body)
        self.show(result)
        self.say(
            "Keep the share code privately; the server returns it only on creation.",
            "請私下保存分享碼，伺服器只會在建立時提供。",
        )

    def join_challenge(self) -> None:
        share = quote(self.ask("Share code: ", "分享碼：", hidden=True), safe="")
        self.show(self.client.request("GET", f"/v1/challenges/{share}"))
        practice = self.yes("Use an unranked replay?", "使用不排名重玩模式？")
        self.play(
            self.client.request("POST", f"/v1/challenges/{share}/start", {"practice": practice})
        )

    def challenge_results(self) -> None:
        identifier = quote(self.ask("Challenge ID: ", "挑戰 ID："), safe="")
        self.browse(f"/v1/challenges/{identifier}/results")

    def revoke_challenge(self) -> None:
        identifier = quote(self.ask("Challenge ID: ", "挑戰 ID："), safe="")
        if self.yes("Revoke this challenge?", "撤銷這項挑戰？"):
            self.client.request("DELETE", f"/v1/challenges/{identifier}")
            self.say("Challenge revoked.", "已撤銷挑戰。")

    def rooms(self) -> None:
        self.menu(
            "Live private duels",
            "即時私人對戰",
            [
                ("Create room", "建立房間", self.create_room),
                ("Join with room code", "使用房間碼加入", self.join_room),
                ("Resume room by ID", "使用 ID 繼續房間", self.resume_room),
            ],
        )

    def create_room(self) -> None:
        difficulty, _ = self.difficulty(custom=False)
        room = self.create_resource(
            "/v1/rooms", {"difficulty": difficulty, "idempotencyKey": uuid.uuid4().hex}
        )
        self.room(room)

    def join_room(self) -> None:
        code = quote(self.ask("Room code: ", "房間碼：", hidden=True), safe="")
        self.room(self.client.request("POST", f"/v1/rooms/{code}/join"))

    def resume_room(self) -> None:
        identifier = quote(self.ask("Room ID: ", "房間 ID："), safe="")
        self.room(self.client.request("GET", f"/v1/rooms/{identifier}"))

    def room(self, room: JSON) -> None:
        identifier = quote(str(room["id"]), safe="")
        self.show(room)
        self.say(
            "Keep the room ID to reconnect. Both players must mark ready.",
            "請保存房間 ID 以便重新連線，雙方都必須準備就緒。",
        )
        with DuelConnection(self.client, identifier, on_event=self.show) as connection:
            while True:
                while True:
                    try:
                        event = connection.events.get_nowait()
                    except queue.Empty:
                        break
                    if event.get("type") in {"attempt_result", "error"}:
                        member = next(
                            (m for m in room["members"] if m["userId"] == self.client.user["id"]),
                            None,
                        )
                        if member and member.get("gameId"):
                            self.save_pending(str(member["gameId"]), None)
                    self.show(event)
                room = self.client.request("GET", f"/v1/rooms/{identifier}")
                mine = next(
                    (
                        member
                        for member in room["members"]
                        if member["userId"] == self.client.user["id"]
                    ),
                    None,
                )
                game_id = str(mine["gameId"]) if mine and mine.get("gameId") else ""
                game = (
                    self.client.request("GET", f"/v1/games/{quote(game_id, safe='')}")
                    if game_id
                    else None
                )
                if game:
                    self.game_board(game)
                if room["status"] in {"completed", "expired", "terminated"}:
                    self.show(room)
                    return
                command = self.ask(
                    "Guess / ready / refresh / retry / abandon / back: ",
                    "猜測／ready 準備／refresh 更新／retry 重試／abandon 放棄／back 返回：",
                )
                action = command.casefold()
                if action in {"back", "quit"}:
                    return
                if action == "ready":
                    self.show(self.client.request("POST", f"/v1/rooms/{identifier}/ready"))
                elif action == "refresh":
                    self.show(room)
                elif action == "abandon" and game_id:
                    if self.yes("Abandon this duel?", "放棄這場對戰？"):
                        self.show(
                            self.client.request(
                                "POST", f"/v1/games/{quote(game_id, safe='')}/abandon"
                            )
                        )
                        self.save_pending(game_id, None)
                elif game and game["status"] == "active":
                    pending = self.pending(game_id)
                    if pending is not None and action != "retry":
                        self.say(
                            "Retry the saved guess before entering another.",
                            "請先重試已儲存的猜測。",
                        )
                        continue
                    try:
                        pending = pending or {
                            "guess": list(normalize_code(command)),
                            "idempotencyKey": uuid.uuid4().hex,
                        }
                        self.save_pending(game_id, pending)
                        connection.send({"version": 1, "type": "guess", **pending})
                        deadline = time.monotonic() + 15
                        while time.monotonic() < deadline:
                            event = connection.events.get(
                                timeout=max(0.01, deadline - time.monotonic())
                            )
                            self.show(event)
                            if event.get("type") in {"attempt_result", "error"}:
                                self.save_pending(game_id, None)
                                break
                        else:
                            raise queue.Empty
                    except queue.Empty:
                        self.say(
                            "No acknowledgement yet. Retry keeps the original key.",
                            "尚未收到確認，重試會保留原本的識別碼。",
                        )
                    except (OnlineError, DomainError) as exc:
                        self.say(str(exc))
                else:
                    self.say(
                        "Waiting for both players, or your game is complete. Use refresh.",
                        "正在等待雙方，或您的遊戲已完成，請使用 refresh。",
                    )

    def profile(self) -> None:
        self.menu(
            "Profile and achievements",
            "個人檔案及成就",
            [
                (
                    "View profile",
                    "查看個人檔案",
                    lambda: self.show(self.client.request("GET", "/v1/me/profile")),
                ),
                (
                    "Statistics and achievements",
                    "統計及成就",
                    lambda: self.show(self.client.request("GET", "/v1/me/stats")),
                ),
                ("Update display name", "更新顯示名稱", self.rename),
                ("Public leaderboard opt-in", "公開排行榜選項", self.leaderboard_opt_in),
            ],
        )

    def rename(self) -> None:
        name = self.ask("Display name (blank removes name): ", "顯示名稱（留空刪除名稱）：")
        self.show(self.client.request("PATCH", "/v1/me/profile", {"displayName": name or None}))

    def leaderboard_opt_in(self) -> None:
        enabled = self.yes("Appear on public leaderboards?", "顯示於公開排行榜？")
        self.show(self.client.request("PATCH", "/v1/me/profile", {"publicLeaderboards": enabled}))

    def leaderboard(self) -> None:
        period = (
            "weekly"
            if self.yes("Weekly leaderboard? (No = all-time)", "每週排行榜？（否＝所有時間）")
            else "all-time"
        )
        self.say(
            "0 All difficulties / 1 Easy / 2 Normal / 3 Hard / 4 Expert",
            "0 全部難度／1 容易／2 普通／3 困難／4 專家",
        )
        choice = self.number("Difficulty: ", "難度：", 0, 4)
        filters: JSON = {"period": period}
        if choice:
            filters["difficulty"] = ("easy", "normal", "hard", "expert")[choice - 1]
        self.browse("/v1/leaderboards", filters)

    def account(self) -> None:
        self.show({"user": self.client.user})
        self.menu(
            "Account controls",
            "帳戶控制",
            [
                ("Request email sign-in / guest upgrade", "要求電郵登入／升級訪客帳戶", self.email),
                ("Verify email link", "驗證電郵連結", self.verify_email),
                ("Set up authenticator MFA", "設定驗證器雙重認證", self.setup_mfa),
                ("Verify MFA / elevate session", "驗證雙重認證／提升工作階段", self.verify_mfa),
                ("Export account ZIP", "匯出帳戶 ZIP", self.export_account),
                ("Delete account permanently", "永久刪除帳戶", self.delete_account),
                ("Sign out and continue as a new guest", "登出並以新訪客身份繼續", self.sign_out),
            ],
        )

    def email(self) -> None:
        email = self.ask("Email: ", "電郵：")
        self.client.request("POST", "/v1/auth/email", {"email": email, "next": "/en/profile"})
        self.say(
            "Check your email. Paste its link into Verify email link without opening it first.",
            "請查看電郵，先不要開啟連結，將它貼到「驗證電郵連結」。",
        )

    def verify_email(self) -> None:
        self.client.verify_email(
            self.ask("One-time email link (hidden): ", "一次性電郵連結（隱藏輸入）：", hidden=True)
        )
        self.show({"user": self.client.user})

    def setup_mfa(self) -> None:
        if self.yes(
            "Set up MFA? This replaces any current authenticator secret.",
            "設定雙重認證？此操作會取代現有驗證器密鑰。",
        ):
            result = self.client.request("POST", "/v1/auth/mfa/totp/setup")
            self.say(
                "Add this private key or URI to your authenticator, then verify a code.",
                "請將以下私密密鑰或 URI 加入驗證器，然後驗證代碼。",
            )
            self.show(result)
            self.verify_mfa()

    def verify_mfa(self) -> None:
        self.client.verify_totp(
            self.ask("Six-digit authenticator code: ", "六位數驗證器代碼：", hidden=True)
        )
        self.say("MFA verified.", "雙重認證驗證成功。")

    def export_account(self) -> None:
        path = Path(
            self.ask(
                "Export ZIP path [cipherboard-data.zip]: ", "匯出 ZIP 路徑 [cipherboard-data.zip]："
            )
            or "cipherboard-data.zip"
        ).expanduser()
        overwrite = path.exists() and self.yes("Replace the existing export?", "取代現有匯出檔案？")
        if path.exists() and not overwrite:
            return
        self.client.download("/v1/me/export", path, overwrite=overwrite)
        self.say(f"Export saved to {path}.", f"匯出已儲存至 {path}。")

    def delete_account(self) -> None:
        confirmation = self.ask(
            "Permanent deletion: type DELETE to confirm: ", "永久刪除：輸入 DELETE 確認："
        )
        if confirmation != "DELETE":
            self.say("Deletion cancelled.", "已取消刪除。")
            return
        self.client.request("DELETE", "/v1/me", {"confirmation": confirmation})
        self.client.logout(remote=False)
        self.say("Account deleted. Continuing as a new guest.", "帳戶已刪除，將以新訪客身份繼續。")
        self.client.connect()

    def sign_out(self) -> None:
        self.client.logout()
        self.client.connect()
        self.say("Signed out. A new guest session is active.", "已登出，新的訪客工作階段已啟用。")

    def settings(self) -> None:
        language = self.number(
            "Language: 1 English  2 繁體中文: ", "語言：1 English  2 繁體中文：", 1, 2
        )
        self.client.state.set_preference("locale", "en" if language == 1 else "zh-Hant")
        theme = self.number(
            "Appearance: 1 System  2 Light  3 Dark  4 Plain: ",
            "外觀：1 系統  2 淺色  3 深色  4 純文字：",
            1,
            4,
        )
        self.client.state.set_preference("theme", ("system", "light", "dark", "plain")[theme - 1])
        peg_style = self.number(
            "Peg style: 1 Letters  2 Letters with patterns  3 High contrast: ",
            "顏色顯示：1 字母  2 字母及圖案編號  3 高對比：",
            1,
            3,
        )
        self.client.state.set_preference(
            "pegStyle", ("symbols", "patterns", "highContrast")[peg_style - 1]
        )
        self.client.state.set_preference("reducedMotion", True)
        self.client.state.set_preference(
            "sound", self.yes("Terminal bell feedback?", "使用終端機提示音？")
        )
        self.client.state.set_preference(
            "analytics",
            self.yes("Consent to privacy-limited product events?", "同意傳送限制資料的產品事件？"),
        )
        self.say(
            "Letter identifiers and black/white labels are always shown. "
            "Terminal output is static and supports keyboard navigation.",
            "一律顯示顏色字母及黑白釘文字標籤，終端機畫面沒有動畫並支援鍵盤操作。",
        )

    def support(self) -> None:
        topics = ("account", "gameplay", "accessibility", "privacy", "safety", "other")
        self.say(
            "1 Account  2 Gameplay  3 Accessibility  4 Privacy  5 Safety  6 Other",
            "1 帳戶  2 遊戲  3 無障礙  4 私隱  5 安全  6 其他",
        )
        topic = topics[self.number("Topic: ", "主題：", 1, 6) - 1]
        email = self.ask("Reply email: ", "回覆電郵：")
        message = self.ask("Message (10-4000 characters): ", "訊息（10-4000 字元）：")
        if self.yes("Send this support request?", "傳送這項支援請求？"):
            self.show(
                self.client.request(
                    "POST", "/v1/support", {"topic": topic, "replyEmail": email, "message": message}
                )
            )

    def admin(self) -> None:
        self.show(self.client.request("GET", "/v1/admin/summary"))
        self.menu(
            "Administration",
            "管理",
            [
                (
                    "Summary",
                    "摘要",
                    lambda: self.show(self.client.request("GET", "/v1/admin/summary")),
                ),
                ("Games", "遊戲", lambda: self.browse("/v1/admin/games")),
                ("Profiles", "個人檔案", lambda: self.browse("/v1/admin/profiles")),
                ("Rooms", "房間", lambda: self.browse("/v1/admin/rooms")),
                ("Challenges", "挑戰", lambda: self.browse("/v1/admin/challenges")),
                (
                    "Leaderboard review",
                    "排行榜審核",
                    lambda: self.browse("/v1/admin/leaderboard-review"),
                ),
                (
                    "Feature flags",
                    "功能開關",
                    lambda: self.show(self.client.request("GET", "/v1/admin/flags")),
                ),
                (
                    "Audit events",
                    "審計事件",
                    lambda: self.show(self.client.request("GET", "/v1/admin/audit?limit=100")),
                ),
                ("Moderation / feature action", "審核／功能操作", self.admin_action),
            ],
        )

    def admin_action(self) -> None:
        actions = (
            ("leaderboard", "invalidate"),
            ("leaderboard", "restore"),
            ("profiles", "moderate"),
            ("profiles", "moderate"),
            ("profiles", "moderate"),
            ("challenges", "revoke"),
            ("rooms", "terminate"),
            ("flags", ""),
        )
        self.say(
            "1 Invalidate score  2 Restore score  3 Restrict account  4 Unrestrict account  "
            "5 Rename profile  6 Revoke challenge  7 Terminate room  8 Change flag",
            "1 取消分數  2 恢復分數  3 限制帳戶  4 解除限制  5 更改名稱  "
            "6 撤銷挑戰  7 終止房間  8 更改功能開關",
        )
        choice = self.number("Action: ", "操作：", 1, 8)
        target = quote(self.ask("Target ID / flag key: ", "目標 ID／功能鍵："), safe="")
        reason = self.ask("Reason (3-300 characters): ", "原因（3-300 字元）：")
        body: JSON = {"reason": reason}
        if choice in {3, 4}:
            body["enabled"] = choice == 3
        elif choice == 5:
            body["displayName"] = self.ask("New display name: ", "新顯示名稱：")
        elif choice == 8:
            body["enabled"] = self.yes("Enable flag?", "啟用功能？")
        area, operation = actions[choice - 1]
        path = f"/v1/admin/{area}/{target}" + (f"/{operation}" if operation else "")
        if self.yes("Apply this administrative change?", "套用這項管理變更？"):
            self.show(self.client.request("PATCH" if choice == 8 else "POST", path, body))

    def guide(self) -> None:
        self.say(
            "Black: correct colour and position. White: correct colour, wrong position. "
            "Invalid guesses consume no attempt. Online play requires the API; "
            "back preserves a resumable game, abandon ends it. "
            "Local CSV scores remain separate from account competition.",
            "黑釘：顏色及位置正確。白釘：顏色正確但位置錯誤。無效猜測不扣次數。"
            "線上遊戲需要 API；back 保留遊戲以便繼續，abandon 結束遊戲。"
            "本機 CSV 分數與帳戶競賽分開保存。",
        )
        self.say(
            "Account credentials and unacknowledged guesses stay in a private local session file. "
            "Active secrets are not saved there. Export and deletion retain server account "
            "and recent-authentication requirements.",
            "帳戶憑證及尚未確認的猜測儲存於本機私密工作階段檔案，並不保存進行中的秘密密碼。匯出及刪除仍須符合伺服器帳戶及近期認證要求。",
        )
        self.say(
            f"Privacy: {self.client.product_origin}/en/privacy\n"
            f"Terms: {self.client.product_origin}/en/terms"
        )
        self.menu(
            "Published policies",
            "已發佈政策",
            [
                ("Read privacy policy", "閱讀私隱政策", lambda: self.policy("privacy")),
                ("Read terms", "閱讀使用條款", lambda: self.policy("terms")),
            ],
        )

    def policy(self, name: str) -> None:
        if name not in {"privacy", "terms"}:
            raise ValueError("Unsupported policy")
        locale = self.client.state.preference("locale", "en")
        if locale not in {"en", "zh-Hant"}:
            locale = "en"
        try:
            # Use a separate, unauthenticated request; never forward API cookies or bearer tokens.
            response = httpx.get(
                f"{self.client.product_origin}/{locale}/{name}",
                timeout=10,
                follow_redirects=False,
            )
        except httpx.TransportError as exc:
            raise OnlineError(
                "POLICY_UNAVAILABLE", "Cannot reach the published policy page."
            ) from exc
        if response.status_code != 200 or len(response.content) > 1_048_576:
            raise OnlineError("POLICY_UNAVAILABLE", "The published policy page is unavailable.")
        parser = PageText()
        parser.feed(response.text)
        content = "\n".join(" ".join(line.split()) for line in "".join(parser.parts).splitlines())
        if not content.strip():
            raise OnlineError(
                "POLICY_UNAVAILABLE", "The page did not contain readable policy text."
            )
        self.say(content)
