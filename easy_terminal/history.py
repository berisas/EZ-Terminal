from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def save_history(input_text: str, commands: list[list[str]], risk: str, root: Path | None = None) -> None:
    base = root or Path.cwd()
    history_dir = base / ".easy"
    history_dir.mkdir(exist_ok=True)
    history_path = history_dir / "history.json"

    records = []
    if history_path.exists():
        try:
            records = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []

    records.append(
        {
            "input": input_text,
            "commands": [_display_command(command) for command in commands],
            "risk": risk,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    history_path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def _display_command(command: list[str]) -> str:
    return " ".join(_quote(part) for part in command)


def _quote(part: str) -> str:
    if not part:
        return '""'
    if any(char.isspace() for char in part) or '"' in part:
        return '"' + part.replace('"', '\\"') + '"'
    return part
