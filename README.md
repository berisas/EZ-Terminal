# Easy Terminal

Easy Terminal is a rule-based fuzzy command resolver for loose but command-centered terminal syntax.

```bash
easy doc
easy git commit game project recent
easy python run voice server
easy open resume pdf
easy find big videos downloads
```

The user still starts with a real command family. Easy Terminal helps resolve paths, files, flags, commit messages, and common formatting.

## Install for local development

```bash
pip install -e ".[dev]"
```

## Supported MVP commands

- `easy git status`
- `easy doc`
- `easy git commit <context>`
- `easy git push [context]`
- `easy python run <context>`
- `easy open <context>`
- `easy find <context>`

Executed commands are logged to `.easy/history.json`.
