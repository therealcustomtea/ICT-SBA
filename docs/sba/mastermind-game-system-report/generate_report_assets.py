#!/usr/bin/env python3
# ruff: noqa: E501
"""Generate diagrams, charts, code captures, and terminal figures for the SBA report."""

from __future__ import annotations

import json
import keyword
import math
import re
import textwrap
from itertools import pairwise
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

W, H = 1800, 1050
INK = "#2D2422"
BROWN = "#513A34"
CORAL = "#E56B5D"
BLUE = "#4BA9C8"
YELLOW = "#E7B84B"
GREEN = "#568A73"
RED = "#B84C4C"
IVORY = "#FBF7EF"
PAPER = "#FFFFFF"
MUTED = "#756B67"
LINE = "#D7CEC5"
PALE_BLUE = "#EAF5F8"
PALE_CORAL = "#FBEDEA"
PALE_YELLOW = "#FBF4DF"
PALE_GREEN = "#EAF3EE"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size=size)


def canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), IVORY)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((38, 34, W - 38, H - 34), radius=28, fill=PAPER, outline=LINE, width=3)
    draw.text((86, 66), title, font=font(44, bold=True), fill=BROWN)
    if subtitle:
        draw.text((88, 124), subtitle, font=font(24), fill=MUTED)
    draw.line((86, 174, W - 86, 174), fill=LINE, width=3)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(ASSETS / name, dpi=(220, 220), optimize=True)


def centered(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    size: int,
    *,
    fill: str = INK,
    bold: bool = False,
) -> None:
    x1, y1, x2, y2 = box
    f = font(size, bold=bold)
    wrapped = textwrap.wrap(text, width=max(10, int((x2 - x1) / (size * 0.62))))
    line_h = size * 1.25
    total_h = len(wrapped) * line_h
    y = (y1 + y2 - total_h) / 2
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=f)
        draw.text(((x1 + x2 - (bbox[2] - bbox[0])) / 2, y), line, font=f, fill=fill)
        y += line_h


def card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    *,
    accent: str = BLUE,
    fill: str = PAPER,
) -> None:
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=accent, width=4)
    x1, y1, x2, _ = box
    draw.rounded_rectangle((x1, y1, x2, y1 + 62), radius=22, fill=accent)
    draw.rectangle((x1, y1 + 38, x2, y1 + 62), fill=accent)
    centered(draw, (x1 + 16, y1 + 4, x2 - 16, y1 + 59), title, 26, fill=PAPER, bold=True)
    centered(draw, (x1 + 28, y1 + 76, x2 - 28, box[3] - 18), body, 22, fill=INK)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    colour: str = BROWN,
    width: int = 6,
) -> None:
    draw.line((*start, *end), fill=colour, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 20
    for offset in (2.55, -2.55):
        point = (
            end[0] + length * math.cos(angle + offset),
            end[1] + length * math.sin(angle + offset),
        )
        draw.line((*end, *point), fill=colour, width=width)


def architecture() -> None:
    image, draw = canvas(
        "CLI-centred system architecture", "One canonical rules engine, two delivery interfaces"
    )
    card(
        draw,
        (95, 260, 445, 500),
        "Player",
        "keyboard input\nterminal feedback",
        accent=CORAL,
        fill=PALE_CORAL,
    )
    card(
        draw,
        (545, 230, 975, 530),
        "mastermind_cli",
        "menu + game loop\nvalidation prompts\nboard history",
        accent=BROWN,
    )
    card(
        draw,
        (1090, 230, 1705, 530),
        "mastermind_core",
        "models | presets | validation\nfeedback | engine | scoring",
        accent=BLUE,
        fill=PALE_BLUE,
    )
    card(
        draw,
        (545, 675, 975, 930),
        "CSVScoreStore",
        "UTF-8 scores\nsafe append + sorted read\natomic export",
        accent=GREEN,
        fill=PALE_GREEN,
    )
    card(
        draw,
        (1090, 675, 1705, 930),
        "FastAPI product",
        "imports the same core\nadds auth, database, realtime",
        accent=YELLOW,
        fill=PALE_YELLOW,
    )
    arrow(draw, (445, 380), (545, 380))
    arrow(draw, (975, 380), (1090, 380))
    arrow(draw, (755, 530), (755, 675))
    arrow(draw, (1395, 530), (1395, 675))
    save(image, "architecture.png")


def cli_flow() -> None:
    image, draw = canvas(
        "Program control flow",
        "The menu remains responsive after valid, invalid, and failed operations",
    )
    nodes = [
        ((690, 215, 1110, 315), "Start CLI", BLUE),
        ((690, 365, 1110, 465), "Display five-option menu", BROWN),
        ((120, 580, 420, 735), "Start game", CORAL),
        ((480, 580, 780, 735), "View scores", GREEN),
        ((840, 580, 1140, 735), "View rules", YELLOW),
        ((1200, 580, 1500, 735), "Export CSV", BLUE),
        ((1515, 580, 1715, 735), "Exit", BROWN),
        ((120, 825, 420, 965), "Game loop", CORAL),
        ((690, 825, 1110, 965), "Invalid choice -> explain", RED),
    ]
    for box, text, colour in nodes:
        draw.rounded_rectangle(box, radius=24, fill=PAPER, outline=colour, width=5)
        centered(draw, box, text, 27, bold=True)
    arrow(draw, (900, 315), (900, 365))
    for target_x in (270, 630, 990, 1350, 1615):
        arrow(draw, (900, 465), (target_x, 580), colour=MUTED, width=4)
    arrow(draw, (270, 735), (270, 825))
    arrow(draw, (900, 465), (900, 825), colour=RED, width=4)
    draw.text((1085, 475), "choice 1-5", font=font(22), fill=MUTED)
    save(image, "cli_flow.png")


def ipo_cycle() -> None:
    image, draw = canvas(
        "Input-Process-Output cycle",
        "Every accepted attempt follows the same deterministic pipeline",
    )
    items = [
        (
            (90, 300, 530, 820),
            "INPUT",
            "Player name\nDifficulty/custom settings\nSecret (hidden if human)\nGuess or quit",
            CORAL,
            PALE_CORAL,
        ),
        (
            (680, 300, 1120, 820),
            "PROCESS",
            "Normalize tokens\nValidate invariants\nCalculate duplicate-safe feedback\nTransition state\nCalculate terminal score",
            BLUE,
            PALE_BLUE,
        ),
        (
            (1270, 300, 1710, 820),
            "OUTPUT",
            "Attempt history\nBlack/white pegs\nAttempts remaining\nResult + score\nCSV record/export",
            GREEN,
            PALE_GREEN,
        ),
    ]
    for box, title, body, accent, fill in items:
        card(draw, box, title, body, accent=accent, fill=fill)
    arrow(draw, (530, 560), (680, 560))
    arrow(draw, (1120, 560), (1270, 560))
    save(image, "ipo_cycle.png")


def state_machine() -> None:
    image, draw = canvas(
        "Game state transition model", "Terminal states cannot accept another guess"
    )
    states = {
        "created": (170, 500, BLUE),
        "active": (650, 500, CORAL),
        "won": (1240, 270, GREEN),
        "lost": (1470, 445, RED),
        "abandoned": (1240, 650, BROWN),
        "expired": (770, 790, YELLOW),
    }
    for label, (x, y, colour) in states.items():
        draw.ellipse((x - 115, y - 62, x + 115, y + 62), fill=PAPER, outline=colour, width=6)
        centered(draw, (x - 110, y - 55, x + 110, y + 55), label.upper(), 25, bold=True)
    arrow(draw, (285, 500), (535, 500))
    arrow(draw, (765, 470), (1125, 295), colour=GREEN)
    arrow(draw, (765, 500), (1355, 455), colour=RED)
    arrow(draw, (750, 550), (1125, 650), colour=BROWN)
    arrow(draw, (690, 560), (780, 730), colour=YELLOW)
    draw.text((350, 450), "create_game", font=font(22), fill=MUTED)
    draw.text((900, 330), "all black", font=font(22), fill=MUTED)
    draw.text((1040, 470), "attempts exhausted", font=font(22), fill=MUTED)
    draw.text((900, 610), "quit", font=font(22), fill=MUTED)
    save(image, "state_machine.png")


def feedback_walkthrough() -> None:
    image, draw = canvas(
        "Duplicate-safe feedback worked example", "Secret R B R G and guess R R B Y"
    )
    colours = {"R": CORAL, "B": BLUE, "G": GREEN, "Y": YELLOW}
    labels = [("SECRET", ["R", "B", "R", "G"], 280), ("GUESS", ["R", "R", "B", "Y"], 440)]
    for label, pegs, y in labels:
        draw.text((160, y + 28), label, font=font(28, bold=True), fill=BROWN)
        for index, peg in enumerate(pegs):
            x = 470 + index * 240
            draw.ellipse((x, y, x + 110, y + 110), fill=colours[peg], outline=BROWN, width=4)
            centered(draw, (x, y, x + 110, y + 110), peg, 34, fill=PAPER, bold=True)
    draw.rounded_rectangle((190, 640, 780, 910), radius=26, fill=PALE_GREEN, outline=GREEN, width=4)
    centered(
        draw,
        (220, 655, 750, 895),
        "1. Remove exact position 1\nBLACK = 1\nUnmatched secret: B R G\nUnmatched guess: R B Y",
        27,
    )
    draw.rounded_rectangle((1010, 640, 1610, 910), radius=26, fill=PALE_BLUE, outline=BLUE, width=4)
    centered(
        draw,
        (1040, 655, 1580, 895),
        "2. Intersect remaining counts\nR = 1, B = 1\nWHITE = 2\nFinal feedback: 1 black, 2 white",
        27,
    )
    arrow(draw, (790, 775), (1000, 775), colour=BROWN)
    save(image, "feedback_walkthrough.png")


def data_model() -> None:
    image, draw = canvas(
        "CLI data model", "Frozen game values separate domain state from file records"
    )
    boxes = [
        (
            (80, 240, 500, 475),
            "GameConfig",
            "colours\ncode_length\nmax_attempts\nduplicates_allowed",
            BLUE,
        ),
        (
            (690, 220, 1110, 500),
            "GameState",
            "mode | status\nattempts tuple\nstarted/completed\nscore",
            CORAL,
        ),
        ((1300, 240, 1720, 475), "AttemptRecord", "number | guess\nFeedback\nsubmitted_at", GREEN),
        (
            (690, 690, 1110, 945),
            "ScoreRecord",
            "player + settings\nattempts + score\nversion + result",
            YELLOW,
        ),
        ((1300, 690, 1720, 945), "CSV row", "13 stable fields\nUTF-8\nno secret code", BROWN),
    ]
    for box, title, body, accent in boxes:
        card(draw, box, title, body, accent=accent)
    arrow(draw, (500, 360), (690, 360))
    arrow(draw, (1110, 360), (1300, 360))
    arrow(draw, (900, 500), (900, 690))
    arrow(draw, (1110, 815), (1300, 815))
    save(image, "data_model.png")


def validation_flow() -> None:
    image, draw = canvas(
        "Guess validation decision flow",
        "Rejected input returns a precise error and consumes no attempt",
    )
    steps = [
        ("Raw input", 105, BLUE),
        ("Empty / quit?", 360, YELLOW),
        ("Separators valid?", 615, YELLOW),
        ("Correct length?", 870, YELLOW),
        ("Known colours?", 1125, YELLOW),
        ("Duplicates allowed?", 1380, YELLOW),
        ("Accepted tuple", 1635, GREEN),
    ]
    y = 440
    for label, x, colour in steps:
        box = (x - 95, y - 70, x + 95, y + 70)
        draw.rounded_rectangle(box, radius=20, fill=PAPER, outline=colour, width=5)
        centered(draw, box, label, 21, bold=True)
    for (_, x1, _), (_, x2, _) in pairwise(steps):
        arrow(draw, (x1 + 95, y), (x2 - 95, y), colour=MUTED, width=4)
    draw.rounded_rectangle((525, 700, 1275, 890), radius=24, fill=PALE_CORAL, outline=RED, width=4)
    centered(
        draw,
        (560, 720, 1240, 870),
        "Any failed check -> DomainError with stable code + safe message\nCLI displays the message, keeps the state active, and asks again",
        27,
    )
    for x in (360, 615, 870, 1125, 1380):
        arrow(draw, (x, 510), (900, 700), colour=RED, width=3)
    save(image, "validation_flow.png")


def csv_pipeline() -> None:
    image, draw = canvas(
        "CSV persistence and export pipeline",
        "Safety checks protect availability, data integrity, and spreadsheet users",
    )
    items = [
        (
            (80, 300, 385, 760),
            "Terminal result",
            "ScoreRecord.now\n13 explicit fields\nsecret excluded",
            CORAL,
        ),
        (
            (460, 300, 765, 760),
            "Sanitize",
            "csv_safe prefixes\nformula-like values\nUTF-8 + newline=''",
            YELLOW,
        ),
        ((840, 300, 1145, 760), "Persist", "create directory\nheader once\nflush + fsync", GREEN),
        (
            (1220, 300, 1525, 760),
            "Read/sort",
            "skip malformed rows\nscore desc\nattempts asc",
            BLUE,
        ),
        ((1560, 300, 1740, 760), "Export", "temporary file\nos.replace\natomic result", BROWN),
    ]
    for box, title, body, colour in items:
        card(draw, box, title, body, accent=colour)
    for a, b in pairwise(items):
        arrow(draw, (a[0][2], 530), (b[0][0], 530), colour=MUTED, width=4)
    save(image, "csv_pipeline.png")


def horizontal_bars(
    name: str,
    title: str,
    subtitle: str,
    rows: list[tuple[str, float, str]],
    maximum: float,
    suffix: str = "",
) -> None:
    image, draw = canvas(title, subtitle)
    left, right = 420, 1640
    y = 250
    for label, value, colour in rows:
        draw.text((105, y + 16), label, font=font(27, bold=True), fill=INK)
        draw.rounded_rectangle((left, y, right, y + 65), radius=20, fill="#EEE8E1")
        end = left + int((right - left) * value / maximum)
        draw.rounded_rectangle((left, y, end, y + 65), radius=20, fill=colour)
        draw.text((end + 18, y + 15), f"{value:g}{suffix}", font=font(26, bold=True), fill=BROWN)
        y += 140
    save(image, name)


def charts() -> None:
    horizontal_bars(
        "presets_chart.png",
        "Official difficulty presets",
        "Code length and palette size rise while attempts become more constrained",
        [
            ("Easy - attempts", 12, GREEN),
            ("Normal - attempts", 10, BLUE),
            ("Hard - attempts", 8, CORAL),
            ("Expert - attempts", 8, BROWN),
        ],
        12,
    )
    horizontal_bars(
        "coverage_chart.png",
        "Measured branch-aware coverage",
        "56 focused core/CLI tests; overall selected-package coverage is 92%",
        [
            ("mastermind_core", 99, GREEN),
            ("CLI storage", 97, BLUE),
            ("CLI entry point", 83, YELLOW),
            ("CLI application", 75, CORAL),
        ],
        100,
        "%",
    )
    image, draw = canvas(
        "Verification evidence", "Results measured on 1 September 2026 using Python 3.13.14"
    )
    metrics = [
        ("Python suite", "117 passed", GREEN),
        ("Browser E2E", "36 passed", BLUE),
        ("Browser cases", "8 skipped", YELLOW),
        ("Core + CLI", "56 passed", BLUE),
        ("Focused coverage", "92%", CORAL),
        ("Ruff + mypy", "passed", GREEN),
    ]
    for index, (label, value, colour) in enumerate(metrics):
        col, row = index % 3, index // 3
        x1, y1 = 105 + col * 555, 260 + row * 345
        box = (x1, y1, x1 + 480, y1 + 260)
        draw.rounded_rectangle(box, radius=28, fill=PAPER, outline=colour, width=5)
        centered(draw, (x1 + 20, y1 + 35, x1 + 460, y1 + 135), value, 43, fill=colour, bold=True)
        centered(draw, (x1 + 20, y1 + 145, x1 + 460, y1 + 230), label, 27, fill=INK)
    save(image, "test_results.png")
    image, draw = canvas("score_v1 composition", "Example: Normal difficulty won in four attempts")
    parts = [
        ("Attempts", 700, CORAL),
        ("Code length", 200, BLUE),
        ("Palette", 120, GREEN),
        ("Duplicates", 100, YELLOW),
    ]
    total = sum(value for _, value, _ in parts)
    x = 160
    for label, value, colour in parts:
        width = int(1480 * value / total)
        draw.rectangle((x, 360, x + width, 590), fill=colour)
        centered(draw, (x + 8, 375, x + width - 8, 505), str(value), 34, fill=PAPER, bold=True)
        centered(draw, (x + 8, 505, x + width - 8, 580), label, 20, fill=PAPER, bold=True)
        x += width
    centered(
        draw,
        (300, 690, 1500, 900),
        "(10 - 4 + 1) x 100 + 4 x 50 + 6 x 20 + 100 = 1,120 points",
        34,
        bold=True,
    )
    save(image, "scoring_chart.png")


def gantt() -> None:
    image, draw = canvas(
        "Project Gantt chart", "Twelve-week iterative development and evidence cycle"
    )
    tasks = [
        ("Problem definition", 1, 2, CORAL),
        ("Analysis + constraints", 2, 3, YELLOW),
        ("Core design", 3, 5, BLUE),
        ("CLI implementation", 5, 7, BROWN),
        ("CSV persistence", 6, 8, GREEN),
        ("Unit + integration tests", 7, 10, CORAL),
        ("Debugging + hardening", 9, 11, YELLOW),
        ("Documentation + evaluation", 10, 12, BLUE),
    ]
    left, top = 500, 250
    cell = 95
    for week in range(1, 13):
        x = left + (week - 1) * cell
        centered(draw, (x, 205, x + cell, 250), f"W{week}", 20, bold=True)
        draw.line((x, top, x, 930), fill=LINE, width=2)
    draw.line((left + 12 * cell, top, left + 12 * cell, 930), fill=LINE, width=2)
    for row, (label, start, end, colour) in enumerate(tasks):
        y = top + row * 82
        draw.text((90, y + 18), label, font=font(23, bold=True), fill=INK)
        draw.rounded_rectangle(
            (left + (start - 1) * cell + 5, y + 8, left + end * cell - 5, y + 60),
            radius=18,
            fill=colour,
        )
    save(image, "gantt_chart.png")


def module_graph() -> None:
    image, draw = canvas(
        "Module relationship graph",
        "The CLI depends inward on pure rules; persistence remains at the edge",
    )
    nodes = {
        "app.py": (280, 500, CORAL),
        "storage.py": (650, 760, GREEN),
        "models.py": (940, 300, BLUE),
        "validation.py": (1310, 250, YELLOW),
        "feedback.py": (1510, 520, CORAL),
        "engine.py": (1110, 640, BROWN),
        "scoring.py": (850, 850, GREEN),
        "presets.py": (580, 280, BLUE),
    }
    edges = [
        ("app.py", "storage.py"),
        ("app.py", "presets.py"),
        ("app.py", "engine.py"),
        ("app.py", "models.py"),
        ("engine.py", "models.py"),
        ("engine.py", "validation.py"),
        ("engine.py", "feedback.py"),
        ("engine.py", "scoring.py"),
        ("presets.py", "models.py"),
    ]
    for source, target in edges:
        sx, sy, _ = nodes[source]
        tx, ty, _ = nodes[target]
        arrow(draw, (sx, sy), (tx, ty), colour="#B7AAA0", width=4)
    for label, (x, y, colour) in nodes.items():
        draw.ellipse((x - 105, y - 54, x + 105, y + 54), fill=PAPER, outline=colour, width=5)
        centered(draw, (x - 100, y - 49, x + 100, y + 49), label, 23, bold=True)
    save(image, "module_graph.png")


def code_image(source: Path, start: int, end: int, name: str, title: str) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()[start - 1 : end]
    image = Image.new("RGB", (1900, 1150), "#17212B")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (24, 24, 1876, 1126), radius=26, fill="#1F2B37", outline="#3A4B5A", width=3
    )
    draw.ellipse((58, 52, 78, 72), fill=CORAL)
    draw.ellipse((90, 52, 110, 72), fill=YELLOW)
    draw.ellipse((122, 52, 142, 72), fill=GREEN)
    draw.text((175, 44), title, font=font(28, bold=True), fill="#E8EEF2")
    draw.text(
        (1510, 48), f"{source.relative_to(ROOT)}:{start}", font=font(20, mono=True), fill="#90A4AE"
    )
    mono = font(22, mono=True)
    y = 105
    keywords = set(keyword.kwlist) | {"True", "False", "None"}
    token_re = re.compile(r"(#[^\n]*|'[^']*'|\"[^\"]*\"|\b\d+\b|\b[A-Za-z_][A-Za-z0-9_]*\b)")
    for number, line in enumerate(lines, start=start):
        draw.text((58, y), f"{number:>4}", font=mono, fill="#607D8B")
        x = 135
        cursor = 0
        for match in token_re.finditer(line):
            plain = line[cursor : match.start()]
            draw.text((x, y), plain, font=mono, fill="#D8DEE9")
            x += draw.textlength(plain, font=mono)
            token = match.group(0)
            colour = "#81A1C1"
            if token.startswith("#"):
                colour = "#7F8C8D"
            elif token.startswith(("'", '"')):
                colour = "#A3BE8C"
            elif token in keywords:
                colour = "#B48EAD"
            elif token.isdigit():
                colour = "#D08770"
            draw.text((x, y), token, font=mono, fill=colour)
            x += draw.textlength(token, font=mono)
            cursor = match.end()
        draw.text((x, y), line[cursor:], font=mono, fill="#D8DEE9")
        y += 34
        if y > 1090:
            break
    save(image, name)


def terminal_image(name: str, title: str, transcript: str) -> None:
    lines = transcript.strip("\n").splitlines()
    height = max(720, 150 + len(lines) * 36)
    image = Image.new("RGB", (1900, height), "#11181F")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (24, 24, 1876, height - 24), radius=26, fill="#18232D", outline="#364955", width=3
    )
    draw.ellipse((58, 52, 78, 72), fill=CORAL)
    draw.ellipse((90, 52, 110, 72), fill=YELLOW)
    draw.ellipse((122, 52, 142, 72), fill=GREEN)
    draw.text((175, 43), title, font=font(28, bold=True), fill="#E8EEF2")
    mono = font(24, mono=True)
    y = 110
    for line in lines:
        colour = "#D7E0E6"
        if line.startswith("$"):
            colour = "#8FD5B0"
        elif "Warning" in line or "Enter a number" in line:
            colour = "#F2C56B"
        elif "Code broken" in line or "passed" in line or "exported" in line:
            colour = "#8FD5B0"
        draw.text((60, y), line, font=mono, fill=colour)
        y += 36
    image.save(ASSETS / name, dpi=(220, 220), optimize=True)


def code_and_terminal_assets() -> None:
    code_image(
        ROOT / "packages/mastermind_core/mastermind_core/feedback.py",
        8,
        25,
        "code_feedback.png",
        "Duplicate-safe feedback function",
    )
    code_image(
        ROOT / "apps/cli/mastermind_cli/app.py",
        40,
        73,
        "code_cli_menu.png",
        "Five-option menu and dispatch loop",
    )
    code_image(
        ROOT / "packages/mastermind_core/mastermind_core/validation.py",
        9,
        50,
        "code_validation.png",
        "Input normalization and rule validation",
    )
    code_image(
        ROOT / "packages/mastermind_core/mastermind_core/engine.py",
        29,
        81,
        "code_submit_guess.png",
        "Immutable attempt transition",
    )
    code_image(
        ROOT / "apps/cli/mastermind_cli/storage.py",
        89,
        137,
        "code_storage.png",
        "Defensive CSV read and atomic export",
    )
    terminal_image(
        "terminal_menu.png",
        "Cipherboard CLI - menu validation",
        "$ uv run python -m mastermind_cli\nMastermind Logic Lab\n\n1. Start game\n2. View local high scores\n3. View rules\n4. Export scores\n5. Exit\nChoose an option: 9\nEnter a number from 1 to 5.\nChoose an option: 3\nMastermind rules\nA black peg means the right colour is in the right position.\nA white peg means the right colour is in a different position.",
    )
    terminal_image(
        "terminal_game.png",
        "Deterministic example game",
        "Player name: Ada\nChoose difficulty: 2\nAvailable colours: R B G Y W K | Code length: 4 | Attempts: 10\nGuess (10 remaining): R R R R\nAttempt  Guess               Black  White\n      1  R R R R                 1      0\n9 attempts remaining.\nGuess (9 remaining): R B G Y\nAttempt  Guess               Black  White\n      1  R R R R                 1      0\n      2  R B G Y                 4      0\n8 attempts remaining.\nCode broken in 2 attempt(s)!\nScore: 1320",
    )
    terminal_image(
        "terminal_tests.png",
        "Verification run - 1 September 2026",
        "$ CI: uv run pytest --cov=mastermind_core --cov-branch\n117 passed in 19.92s | core coverage 99.72%\n\n$ pnpm test:e2e\n36 passed, 8 skipped\n\n$ uv run pytest tests/core tests/cli --cov=mastermind_core --cov=mastermind_cli\n56 passed in 0.53s\nTOTAL  522 statements  34 missed  118 branches  92%\n\n$ uv run ruff check apps/cli packages/mastermind_core tests/cli tests/core\nAll checks passed!\n\n$ uv run mypy apps/cli packages/mastermind_core\nSuccess: no issues found in 13 source files",
    )


def main() -> None:
    architecture()
    cli_flow()
    ipo_cycle()
    state_machine()
    feedback_walkthrough()
    data_model()
    validation_flow()
    csv_pipeline()
    charts()
    gantt()
    module_graph()
    code_and_terminal_assets()
    manifest = {path.name: path.stat().st_size for path in sorted(ASSETS.glob("*.png"))}
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(manifest)} report figures in {ASSETS}")


if __name__ == "__main__":
    main()
