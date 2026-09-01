#!/usr/bin/env python3
"""Build the guided macOS and Windows installer archives from tracked source areas."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELEASE_VERSION = (
    f"v{json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))['version']}"
)
FULL_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
PAYLOAD_PATHS = (
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "uv.lock",
    "apps/api",
    "apps/cli",
    "apps/web",
    "packages/api_client",
    "packages/shared_config",
    "packages/mastermind_core",
    "infra/docker",
    "installer",
)
EXCLUDED_PARTS = {
    ".git",
    ".next",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".branches",
    ".temp",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
    "output",
    "playwright-report",
    "test-results",
}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path.name in {".DS_Store"} or path.name.endswith((".log", ".tsbuildinfo")):
        return False
    return not any(part in EXCLUDED_PARTS or part.startswith(".env") for part in relative.parts)


def copy_payload(destination: Path) -> None:
    for relative_name in PAYLOAD_PATHS:
        source = ROOT / relative_name
        if not source.exists():
            raise FileNotFoundError(f"Required installer payload is missing: {source}")
        destination_path = destination / relative_name
        if source.is_file():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination_path)
            continue
        for file_path in source.rglob("*"):
            if not file_path.is_file() or not included(file_path):
                continue
            relative_path = file_path.relative_to(ROOT)
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target)


def write_zip(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for file_path in sorted(path for path in source.rglob("*") if path.is_file()):
            relative_path = file_path.relative_to(source)
            info = zipfile.ZipInfo.from_file(file_path, relative_path.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            if (
                file_path.suffix in {".command", ".sh"}
                or "Contents/MacOS" in relative_path.as_posix()
            ):
                info.external_attr = (stat.S_IFREG | 0o755) << 16
            with file_path.open("rb") as input_file:
                archive.writestr(info, input_file.read(), compress_type=zipfile.ZIP_DEFLATED)


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def resolve_source_commit(explicit: str | None = None) -> str:
    candidate = explicit or os.environ.get("GITHUB_SHA")
    if candidate is None:
        git_executable = shutil.which("git")
        if git_executable is None:
            raise RuntimeError("Git is required to record installer source provenance.")
        candidate = subprocess.run(  # noqa: S603 - fixed Git command; no user-controlled arguments
            [git_executable, "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    candidate = candidate.lower()
    if not FULL_GIT_SHA.fullmatch(candidate):
        raise ValueError("Installer source commit must be a full 40-character Git SHA.")
    return candidate


def write_release_note(destination: Path, release_version: str, source_commit: str) -> None:
    (destination / "RELEASE.txt").write_text(
        "\n".join(
            (
                f"Cipherboard {release_version}",
                f"Source commit: {source_commit}",
                "Includes: GUI, CLI, API, MongoDB, Redis, Mailpit, and service launchers.",
                "Install by running the platform installer and choosing the destination folder.",
                "",
            )
        ),
        encoding="utf-8",
    )


def build(
    output_directory: Path,
    *,
    release_version: str = DEFAULT_RELEASE_VERSION,
    source_commit: str | None = None,
) -> list[Path]:
    resolved_commit = resolve_source_commit(source_commit)
    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cipherboard-installers-") as temporary_name:
        temporary = Path(temporary_name)
        payload = temporary / "payload"
        copy_payload(payload)

        mac_stage = temporary / "macOS"
        mac_stage.mkdir()
        shutil.copy2(ROOT / "installer/macos/Install Cipherboard.command", mac_stage)
        shutil.copytree(payload, mac_stage / "payload")
        write_release_note(mac_stage, release_version, resolved_commit)

        windows_stage = temporary / "Windows"
        windows_stage.mkdir()
        shutil.copy2(ROOT / "installer/windows/Install Cipherboard.cmd", windows_stage)
        shutil.copy2(ROOT / "installer/windows/Install-Cipherboard.ps1", windows_stage)
        shutil.copytree(payload, windows_stage / "payload")
        write_release_note(windows_stage, release_version, resolved_commit)

        archives = [
            output_directory / "Cipherboard-macOS.zip",
            output_directory / "Cipherboard-Windows.zip",
        ]
        write_zip(mac_stage, archives[0])
        write_zip(windows_stage, archives[1])

    checksum_file = output_directory / "SHA256SUMS.txt"
    checksum_file.write_text(
        "".join(f"{digest(path)}  {path.name}\n" for path in archives), encoding="utf-8"
    )
    return [*archives, checksum_file]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/installers",
        help="Directory for the two ZIP archives and checksum file",
    )
    parser.add_argument(
        "--release-version",
        default=DEFAULT_RELEASE_VERSION,
        help=f"Release label written into each archive (default: {DEFAULT_RELEASE_VERSION})",
    )
    parser.add_argument(
        "--source-commit",
        help="Full Git commit SHA written into each archive (defaults to GITHUB_SHA or HEAD)",
    )
    arguments = parser.parse_args()
    for artifact in build(
        arguments.output.resolve(),
        release_version=arguments.release_version,
        source_commit=arguments.source_commit,
    ):
        print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
