from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ParsedCommand:
    family: str
    action: str
    context: list[str]
    raw_args: list[str]


@dataclass(frozen=True)
class FileCandidate:
    path: Path
    filename: str
    extension: str
    modified_time: datetime
    created_time: datetime
    folder_names: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    is_git_changed: bool = False


@dataclass(frozen=True)
class Resolution:
    commands: list[list[str]]
    risk: str
    message: str
    dry_output: list[str] = field(default_factory=list)
