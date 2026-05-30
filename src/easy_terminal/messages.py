from __future__ import annotations

import random


def pick(options: list[str]) -> str:
    return random.choice(options)


NOT_A_COMMAND = "Unsupported command. Try easy doc, or start with git, python, open, or find."

GIT_STATUS = [
    "Git status complete.",
    "Repository status checked.",
]

GIT_COMMIT = [
    "Commit complete.",
    "Changes committed.",
    "Selected changes committed successfully.",
]

GIT_PUSH = [
    "Push complete.",
    "Repository pushed.",
]

PYTHON_RUN = [
    "Running Python target.",
    "Python command started.",
]

OPENED = [
    "File opened.",
    "Open command started.",
]

FOUND = [
    "Find command complete.",
    "Search finished.",
]
