from __future__ import annotations

import random


def pick(options: list[str]) -> str:
    return random.choice(options)


NOT_A_COMMAND = "It didn't work :("

GIT_STATUS = [
    "What's the status?",
    "Ok I checked it.",
]

GIT_COMMIT = [
    "Ok i did the commit thing i think.",
    "Commit to a relationship bro.",
    "Ok done.",
]

GIT_PUSH = [
    "Was I supposed to push or pull?",
    "Repository deleted.",
]

PYTHON_RUN = [
    "Running Python target.",
    "Python command started.",
]

OPENED = [
    "Did you really need me to open a file?",
    "Ok man I opened it.",
]

FOUND = [
    "I FOUND IT!!!",
    "Ok I found it for you...",
]
