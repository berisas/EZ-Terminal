from __future__ import annotations

import sys
from pathlib import Path

from easy_terminal import messages
from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import SAFE

VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
ARCHIVE_EXTENSIONS = [".zip", ".tar", ".gz", ".7z", ".rar"]


def resolve(parsed: ParsedCommand) -> Resolution:
    location = _location(parsed.context)
    extensions = _extensions(parsed.context)
    big = any(word in parsed.context for word in {"big", "large", "huge"})
    recent = any(word in parsed.context for word in {"recent", "recently", "today", "newest", "latest"})

    command = _windows_find(location, extensions, big, recent) if sys.platform.startswith("win") else _posix_find(location, extensions, big, recent)
    return Resolution(commands=[command], risk=SAFE, message=messages.pick(messages.FOUND))


def _location(context: list[str]) -> Path:
    home = Path.home()
    if "downloads" in context or "download" in context:
        return home / "Downloads"
    if "desktop" in context:
        return home / "Desktop"
    if "documents" in context or "docs" in context:
        return home / "Documents"
    return Path.cwd()


def _extensions(context: list[str]) -> list[str]:
    words = set(context)
    if words & {"video", "videos", "movie", "movies"}:
        return VIDEO_EXTENSIONS
    if words & {"image", "images", "picture", "pictures", "screenshot", "screenshots"}:
        return IMAGE_EXTENSIONS
    if words & {"python", "py"}:
        return [".py"]
    if words & {"zip", "archive", "archives"}:
        return ARCHIVE_EXTENSIONS
    if "pdf" in words:
        return [".pdf"]
    return []


def _windows_find(location: Path, extensions: list[str], big: bool, recent: bool) -> list[str]:
    filters = []
    if extensions:
        quoted = ", ".join(f"'{extension}'" for extension in extensions)
        filters.append(f"$_.Extension -in @({quoted})")
    if big:
        filters.append("$_.Length -gt 100MB")
    if recent:
        filters.append("$_.LastWriteTime -gt (Get-Date).AddDays(-2)")

    where = ""
    if filters:
        where = " | Where-Object { " + " -and ".join(filters) + " }"

    path = str(location).replace("'", "''")
    script = (
        f"Get-ChildItem -LiteralPath '{path}' -File -Recurse -ErrorAction SilentlyContinue"
        f"{where} | Select-Object -ExpandProperty FullName"
    )
    return ["powershell", "-NoProfile", "-Command", script]


def _posix_find(location: Path, extensions: list[str], big: bool, recent: bool) -> list[str]:
    command = ["find", str(location), "-type", "f"]
    if extensions:
        command.extend(["("])
        for index, extension in enumerate(extensions):
            if index:
                command.extend(["-o"])
            command.extend(["-iname", f"*{extension}"])
        command.extend([")"])
    if big:
        command.extend(["-size", "+100M"])
    if recent:
        command.extend(["-mtime", "-2"])
    return command
