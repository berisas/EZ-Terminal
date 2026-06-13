# Easy Terminal

Easy Terminal is a rule-based fuzzy command resolver for loose but command-centered
terminal syntax.

It is designed for developers who know the command family they want, but want help
resolving paths, files, common flags, commit messages, and routine command formatting.

```bash
easy doc
easy git commit game project recent
easy python run voice server
easy open resume pdf
easy find big videos downloads
```

The user still starts with a real command family. Easy Terminal handles the fuzzy
context after that.

## Project Structure

- `src/easy_terminal/` - Application package and command resolvers.
- `src/easy_terminal/commands/` - Command-family implementations.
- `tests/` - Unit tests for parsing, scoring, resolver behavior, and docs output.
- `.easy/` - Local runtime history, ignored by Git.
- `pyproject.toml` - Package metadata, dependencies, CLI entry point, and test config.

## Install for local development

```bash
pip install -e ".[dev]"
```

## Supported Commands

### Git Commands

Easy Terminal provides fuzzy resolution for comprehensive git workflows:

**Commit & Status:**
- `easy git status`
- `easy git init`
- `easy git commit <context>` (fuzzy file selection)
- `easy git commit all` (current directory only)
- `easy git commit all -m "message"` (explicit message)

**Remote & Publishing:**
- `easy git remote [url]`
- `easy git repo check`
- `easy git push [context]`
- `easy git publish [url]`

**Branch Management:**
- `easy git branch list` (local and remote)
- `easy git branch copy <old> <new>`
- `easy git branch delete <branch>`
- `easy git branch delete <branch> force`
- `easy git branch rename <old> <new>`
- `easy git branch merged` (list merged branches)
- `easy git branch unmerged` (list unmerged branches)
- `easy git switch <branch>` (switch to branch)
- `easy git switch new <branch>` (create and switch)

**Merge & Rebase:**
- `easy git merge <branch>` (standard merge)
- `easy git merge no-ff <branch>` (merge with commit)
- `easy git merge squash <branch>` (squash merge)
- `easy git rebase <branch>` (rebase onto branch)
- `easy git rebase interactive <branch>` (interactive rebase)
- `easy git rebase continue` (continue after conflicts)
- `easy git rebase abort` (abort rebase)

**Pull & History:**
- `easy git pull` (fetch and merge)
- `easy git pull rebase` (fetch and rebase)
- `easy git log` (last 10 commits)
- `easy git log past <count>` (last n commits)
- `easy git log graph` (visual branch history)
- `easy git log diff` (show commit diffs)
- `easy git branch log <branch>` (branch-specific history)

**Inspect Changes:**
- `easy git diff` (unstaged changes)
- `easy git diff staged` (staged changes)
- `easy git diff <branch>` (compare with branch)
- `easy git show <commit>` (commit details)

**Undo & Cleanup:**
- `easy git reset <file>` (unstage file)
- `easy git revert <commit>` (create undo commit)
- `easy git restore <file>` (discard working tree changes)
- `easy git clean untracked` (remove untracked files)

### Other Commands

- `easy doc` - Show documentation
- `easy python run <context>` - Run Python files by context
- `easy open <context>` - Open files by fuzzy match
- `easy find <context>` - Find files and directories

All executed commands are logged to `.easy/history.json`.
