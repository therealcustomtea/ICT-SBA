#!/usr/bin/env python3
"""Extract physical heading pages from a rendered report for the static linked TOC."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).casefold().strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    headings = [
        match.group(2)
        for line in args.source.read_text(encoding="utf-8").splitlines()
        if (match := HEADING_RE.match(line))
    ]
    with pdfplumber.open(args.pdf) as report:
        pages = [normalize(page.extract_text() or "") for page in report.pages]

    page_map: dict[str, int] = {}
    unresolved: list[str] = []
    for index, heading in enumerate(headings, start=1):
        needle = normalize(heading)
        matches = [page_number for page_number, text in enumerate(pages, start=1) if needle in text]
        if matches:
            page_map[f"h_{index}"] = matches[-1]
        else:
            unresolved.append(heading)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(page_map, indent=2) + "\n", encoding="utf-8")
    print(f"mapped={len(page_map)} unresolved={len(unresolved)}")
    for heading in unresolved:
        print(f"UNRESOLVED {heading}")


if __name__ == "__main__":
    main()
