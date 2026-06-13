from __future__ import annotations

from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import SAFE

HELP_TEXT = """Easy Terminal

Use:
  easy <command-family> <action> <loose-context>

Help:
  easy doc
  easy docs
  easy help
      Show this help.

Git setup and publishing:
  easy git status
      Run git status --short.

  easy git repo check
      Show repo root, branch, remotes, and short status.

  easy git init
      Create a Git repo in the current folder.

  easy git remote
      Show configured remotes.

  easy git remote <url>
      Add origin if missing, otherwise update origin to the URL.
      Example: easy git remote https://github.com/you/project.git

  easy git publish <url>
      Rename the current branch to main, add/update origin, and push upstream.

Git commit and push:
  easy git commit <context>
      Fuzzy-match changed files, stage the best match, and commit them.
      Example: easy git commit game project recent

  easy git commit all
      Stage everything under the current folder and commit it.

  easy git commit all -m "Add first version"
      Stage everything under the current folder with your exact commit message.

  easy git commit <context> message <your message>
      Fuzzy-match files with context, then use your exact commit message.

  easy git push
      Run git push.

  easy git push first
      Push the current branch and set origin as upstream.

Git branches and history:
  easy git branch list
      List local and remote branches.

  easy git branch copy <old> <new>
      Copy a branch.

  easy git branch delete <branch>
  easy git branch delete <branch> force
      Delete a branch, optionally forcing deletion.

  easy git branch rename <old> <new>
      Rename a branch.

  easy git branch merged
  easy git branch unmerged
      List merged or unmerged branches.

  easy git branch log <branch>
      Show one-line history for a branch.

  easy git switch <branch>
  easy git switch new <branch>
      Switch branches or create and switch to a new branch.

  easy git log
  easy git log past <count>
  easy git log graph
  easy git log diff
      Show recent history, a count of commits, graph history, or patch history.

Git sync, inspect, and undo:
  easy git pull
  easy git pull rebase
      Pull normally or pull with rebase.

  easy git merge <branch>
  easy git merge no-ff <branch>
  easy git merge squash <branch>
      Merge a branch normally, with a merge commit, or as a squash.

  easy git rebase <branch>
  easy git rebase interactive <branch>
  easy git rebase continue
  easy git rebase abort
      Rebase, interactively rebase, continue, or abort.

  easy git diff
  easy git diff staged
  easy git diff <branch>
      Show unstaged, staged, or branch diffs.

  easy git show <commit>
      Show commit details.

  easy git reset <file>
      Unstage a file.

  easy git restore <file>
      Discard working tree changes for a file.

  easy git revert <commit>
      Create a revert commit.

  easy git clean untracked
      Remove untracked files and directories.

Files and local commands:
  easy make file <name> <type>
      Create a file, including parent folders if needed.
      Examples: easy make file auth py
                easy make file src/config json
                easy make file README md

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
  Start with a real command family: doc, git, python, open, find, or make.
  Loose words after that are for filenames, folders, extensions, and recency.
  Vague assistant-style requests are rejected so generated commands stay predictable.

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
