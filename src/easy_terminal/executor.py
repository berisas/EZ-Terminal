from __future__ import annotations

import subprocess

from easy_terminal.models import Resolution
from easy_terminal.risk import DANGEROUS


class ExecutionError(RuntimeError):
    pass


def execute(resolution: Resolution) -> None:
    if resolution.risk == DANGEROUS:
        raise ExecutionError("dangerous command blocked")

    for command in resolution.commands:
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            raise ExecutionError(f"command failed: {_display_command(command)}")


def _display_command(command: list[str]) -> str:
    return " ".join(command)
