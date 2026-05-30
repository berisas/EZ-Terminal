from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from easy_terminal.models import FileCandidate

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".pytest_cache",
}

MAX_FILES = 3000


def scan_files(
    root: Path | None = None,
    git_changed_paths: set[Path] | None = None,
    max_files: int = MAX_FILES,
) -> list[FileCandidate]:
    base = (root or Path.cwd()).resolve()
    changed = {path.resolve() for path in git_changed_paths or set()}
    candidates: list[FileCandidate] = []

    for current_root, dirs, files in os.walk(base):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        current_path = Path(current_root)

        for filename in files:
            path = current_path / filename
            try:
                candidates.append(candidate_from_path(path, base, path.resolve() in changed))
            except OSError:
                continue

            if len(candidates) >= max_files:
                return candidates

    return candidates


def candidate_from_path(
    path: Path,
    root: Path | None = None,
    is_git_changed: bool = False,
) -> FileCandidate:
    base = (root or Path.cwd()).resolve()
    resolved = path.resolve()
    stat = resolved.stat()

    try:
        relative = resolved.relative_to(base)
    except ValueError:
        relative = resolved

    folder_names = [part.lower() for part in relative.parent.parts if part not in ("", ".")]
    filename = resolved.name
    extension = resolved.suffix.lower()
    keywords = sorted(
        set(
            _tokenize(filename)
            + _tokenize(resolved.stem)
            + _tokenize(extension.lstrip("."))
            + [token for folder in folder_names for token in _tokenize(folder)]
        )
    )

    return FileCandidate(
        path=resolved,
        filename=filename,
        extension=extension,
        modified_time=datetime.fromtimestamp(stat.st_mtime),
        created_time=datetime.fromtimestamp(stat.st_ctime),
        folder_names=folder_names,
        keywords=keywords,
        is_git_changed=is_git_changed,
    )


def _tokenize(value: str) -> list[str]:
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return [part.lower() for part in re.split(r"[^A-Za-z0-9]+", value) if part]
