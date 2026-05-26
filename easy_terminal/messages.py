from __future__ import annotations

import random


def pick(options: list[str]) -> str:
    return random.choice(options)


NOT_A_COMMAND = "not a command. try easy doc, or start with git, python, open, or find."

GIT_STATUS = [
    "yeah what's up",
    "yo",
]

GIT_COMMIT = [
    "okay I did my best",
    "come on bro you really needed me for this?",
    "really? you couldn't even write a commit message?",
]

GIT_PUSH = [
    "did it work?",
    "wait was I supposed to push or pull?",
]

PYTHON_RUN = [
    "running the Python thingy",
    "WE did this",
]

OPENED = [
    "you can't be serious",
    "you need me to open that for you?",
]

FOUND = [
    "we'll ignore what I found looking for this",
    "I like yaoi too man",
]
