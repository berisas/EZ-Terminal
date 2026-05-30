# Easy Terminal Architecture

Easy Terminal is a Python CLI package with a Typer entry point named `easy`.

## Source Layout

- `src/easy_terminal/main.py` defines the CLI entry point.
- `src/easy_terminal/parser.py` validates supported command families and actions.
- `src/easy_terminal/resolver.py` routes parsed input to command-family resolvers.
- `src/easy_terminal/commands/` contains resolver implementations for each command family.
- `src/easy_terminal/scanner.py` discovers local file candidates.
- `src/easy_terminal/scoring.py` ranks candidate files against loose user context.
- `src/easy_terminal/risk.py` classifies command risk.
- `src/easy_terminal/executor.py` runs resolved commands.
- `src/easy_terminal/history.py` writes local command history to `.easy/history.json`.
- `tests/` contains pytest coverage for parser, scoring, docs, and Git resolver behavior.

## Runtime Flow

1. Typer receives arguments from the `easy` console script.
2. `parse_input` rejects unsupported command families and actions.
3. `resolve` dispatches the parsed command to a command-family resolver.
4. The resolver returns a `Resolution` with commands, risk level, and display message.
5. `main.run` blocks dangerous commands.
6. Safe, mild, and risky commands are executed by `executor.execute`.
7. Executed commands are appended to `.easy/history.json`.

## Package Layout

The project uses a `src/` layout so tests and editable installs import the package
the same way production users do.

The package finder is configured in `pyproject.toml`:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Pytest imports from `src` through:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

## Generated Files

The following paths are runtime or build artifacts and should not be committed:

- `.easy/`
- `*.egg-info/`
- `__pycache__/`
- `.pytest_cache/`
- `dist/`
- `build/`
