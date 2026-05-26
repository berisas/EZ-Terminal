from __future__ import annotations

from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import SAFE

HELP_TEXT = """Easy Terminal

Use:
  easy <command-family> <action> <loose-context>

Commands:
  easy doc
      Show this help.

  easy git status
      Run git status --short.

  easy git commit <context>
      Fuzzy-match changed files, stage the best match, and commit them.
      Example: easy git commit game project recent

  easy git push
      Run git push.

  easy python run <context>
      Find the best matching .py file and run it.
      Example: easy python run voice server

  easy open <context>
      Find and open the best matching local file.
      Example: easy open resume pdf

  easy find <context>
      Search files using loose filters like big, recent, videos, downloads.
      Example: easy find big videos downloads

Notes:
  Start with a real command family: git, python, open, find.
  Loose words after that are for filenames, folders, extensions, and recency.
  Vague assistant requests are rejected. Terminal still has standards.
"""


def resolve(parsed: ParsedCommand) -> Resolution:
    return Resolution(commands=[], risk=SAFE, message=HELP_TEXT)
