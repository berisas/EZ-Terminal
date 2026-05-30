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

## Supported MVP commands

- `easy git status`
- `easy doc`
- `easy git repo check`
- `easy git init`
- `easy git remote [url]`
- `easy git commit <context>`
- `easy git commit all`
- `easy git commit all -m "Your message"`
- `easy git push [context]`
- `easy git publish [url]`
- `easy python run <context>`
- `easy open <context>`
- `easy find <context>`

Executed commands are logged to `.easy/history.json`.
