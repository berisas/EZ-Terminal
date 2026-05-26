from __future__ import annotations

from pathlib import Path

from easy_terminal import messages
from easy_terminal.errors import ResolveError
from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import SAFE
from easy_terminal.scanner import scan_files
from easy_terminal.scoring import is_ambiguous, rank_candidates


def resolve(parsed: ParsedCommand) -> Resolution:
    if parsed.action != "run":
        raise ResolveError("sorry I only implemented run")

    candidates = [candidate for candidate in scan_files(Path.cwd()) if candidate.extension == ".py"]
    ranked = rank_candidates(candidates, parsed.context, extension=".py", prefer_entry_files=True)

    if not ranked:
        raise ResolveError("I lost the file sorry.")

    if is_ambiguous(ranked):
        raise ResolveError(_ambiguous("if I was an AI I could probably deduce it:", ranked))

    target = ranked[0][0].path
    return Resolution(
        commands=[["python", _relative(target)]],
        risk=SAFE,
        message=messages.pick(messages.PYTHON_RUN),
    )


def _relative(path: Path) -> str:
    try:
        return "./" + path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def _ambiguous(title: str, ranked) -> str:
    lines = [title]
    for index, (candidate, _) in enumerate(ranked[:5], 1):
        lines.append(f"{index}. {_relative(candidate.path)}")
    lines.append("")
    lines.append("try: easy python run <more specific words>")
    return "\n".join(lines)
