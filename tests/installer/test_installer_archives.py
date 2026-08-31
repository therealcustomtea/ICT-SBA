from __future__ import annotations

import stat
import zipfile
from pathlib import Path

from infra.installers.build_release_archives import build


def test_installer_archives_contain_launchers_and_sanitized_payload(tmp_path: Path) -> None:
    artifacts = build(tmp_path)

    assert [artifact.name for artifact in artifacts] == [
        "Cipherboard-macOS.zip",
        "Cipherboard-Windows.zip",
        "SHA256SUMS.txt",
    ]
    assert "Cipherboard-macOS.zip" in artifacts[2].read_text(encoding="utf-8")
    assert "Cipherboard-Windows.zip" in artifacts[2].read_text(encoding="utf-8")

    with zipfile.ZipFile(artifacts[0]) as archive:
        names = set(archive.namelist())
        assert "Install Cipherboard.command" in names
        assert "payload/installer/docker-compose.yml" in names
        assert "payload/apps/web/package.json" in names
        assert "payload/apps/api/mastermind_api/main.py" in names
        mode = archive.getinfo("Install Cipherboard.command").external_attr >> 16
        assert mode & stat.S_IXUSR

    with zipfile.ZipFile(artifacts[1]) as archive:
        names = set(archive.namelist())
        assert "Install Cipherboard.cmd" in names
        assert "Install-Cipherboard.ps1" in names
        assert "payload/installer/runtime/windows/cipherboard.cmd" in names
        assert not any("/.env" in name or "/node_modules/" in name for name in names)
        assert not any("/supabase/" in name for name in names)
        assert not any(name.endswith(".tsbuildinfo") for name in names)
