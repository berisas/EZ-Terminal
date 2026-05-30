from __future__ import annotations

import os
import sys
from pathlib import Path

from easy_terminal import messages
from easy_terminal.errors import ResolveError
from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import SAFE
from easy_terminal.scanner import scan_files
from easy_terminal.scoring import is_ambiguous, rank_candidates


def resolve(parsed: ParsedCommand) -> Resolution:
    candidates = scan_files(Path.cwd())
    ranked = rank_candidates(candidates, parsed.context)

    if not ranked:
        wanted = " ".join(parsed.context) or "that file"
        raise ResolveError(f"could not find {wanted}.")

    if is_ambiguous(ranked):
        raise ResolveError(_ambiguous(ranked))

    target = ranked[0][0].path
    return Resolution(
        commands=[_open_command(target)],
        risk=SAFE,
        message=messages.pick(messages.OPENED),
    )


def _open_command(path: Path) -> list[str]:
    if sys.platform.startswith("win"):
        return ["cmd", "/c", "start", "", str(path)]
    if sys.platform == "darwin":
        return ["open", str(path)]
    return ["xdg-open", str(path)]


def _relative(path: Path) -> str:
    try:
        return "./" + path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return os.fspath(path)


def _ambiguous(ranked) -> str:
    lines = ["Multiple files matched. Add more specific words:"]
    for index, (candidate, _) in enumerate(ranked[:5], 1):
        lines.append(f"{index}. {_relative(candidate.path)}")
    lines.append("")
    lines.append("try: easy open <more specific words>")
    return "\n".join(lines)
