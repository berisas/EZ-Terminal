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

  easy git repo check
      Show repo root, branch, remotes, and short status.
      Use this before pushing if something feels cursed.

  easy git init
      Create a Git repo in the current folder.

  easy git remote
      Show configured remotes.

  easy git remote <url>
      Add origin if missing, otherwise update origin to the URL.
      Example: easy git remote https://github.com/you/project.git

  easy git commit <context>
      Fuzzy-match changed files, stage the best match, and commit them.
      Example: easy git commit game project recent

  easy git commit all
      Stage everything under the current folder and commit it.
      Example: easy git commit all

  easy git commit all -m "Add first version"
      Stage everything under the current folder with your exact commit message.

  easy git commit <context> message <your message>
      Fuzzy-match files with context, then use your exact commit message.
      Example: easy git commit website message Update homepage layout

  easy git push
      Run git push.

  easy git push first
      Push the current branch and set origin as upstream.

  easy git publish <url>
      Set branch to main, add/update origin, and push with upstream.
      Example: easy git publish https://github.com/you/project.git

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

Quick repo tutorial:
  1. cd into the project folder you want to publish.
  2. Run: easy git repo check
     Make sure the repo root is the project folder, not your home folder.
  3. If it is not a repo yet, run: easy git init
  4. Create an empty GitHub repo with no README/license/gitignore.
  5. Run: easy git remote https://github.com/you/project.git
  6. Run: easy git status
  7. Run: easy git commit all -m "Add first version"
  8. Run: easy git push first
"""


def resolve(parsed: ParsedCommand) -> Resolution:
    return Resolution(commands=[], risk=SAFE, message=HELP_TEXT)
