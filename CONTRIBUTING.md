# Contributing to Easy Terminal

Thank you for your interest in contributing to Easy Terminal! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- pip

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/easy-terminal.git
cd easy-terminal
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode with test dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests to verify setup:
```bash
pytest
```

## Development Workflow

### Code Structure

- `src/easy_terminal/` - Main package
- `src/easy_terminal/commands/` - Command family resolvers
- `tests/` - Pytest test suite
- `docs/` - Documentation (ARCHITECTURE.md)

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

### Adding a New Command Family

1. Create a resolver in `src/easy_terminal/commands/new_family.py`:
```python
def resolve(parsed: ParsedCommand) -> Resolution:
    """Resolve parsed command to execution plan."""
    if parsed.action == "action_name":
        return Resolution(
            commands=[["actual", "command"]],
            risk=SAFE,  # or MILD
            message="User-facing message",
        )
    raise ResolveError("Unsupported action.")
```

2. Register in `src/easy_terminal/parser.py`:
```python
SUPPORTED = {
    ...
    "new_family": {"action_name", "other_action"},
}
```

3. Add import to `src/easy_terminal/resolver.py`

4. Write tests in `tests/test_new_family_resolver.py`

5. Update README.md with command examples

### Adding a New Git Command

1. Add the action to `SUPPORTED["git"]` in `parser.py`
2. Create a `_resolve_<action>()` function in `commands/git.py`
3. Add test cases in `tests/test_git_resolver.py` (follow existing patterns)
4. Update README.md supported commands list
5. Run tests: `pytest tests/test_git_resolver.py -v`

### Testing

- Run all tests:
```bash
pytest
```

- Run specific test file:
```bash
pytest tests/test_git_resolver.py -v
```

- Run with coverage:
```bash
pytest --cov=src/easy_terminal tests/
```

### Code Style

- Follow PEP 8
- Use type hints for function parameters and returns
- Keep functions focused and well-documented
- Include docstrings for all functions explaining purpose, args, returns, and exceptions

### Documentation

- Update README.md when adding new commands
- Update CHANGELOG.md for user-visible changes
- Add docstrings to all functions
- Update ARCHITECTURE.md if changing design patterns

## Testing Requirements

All contributions must:
- Pass `pytest` without errors
- Include tests for new functionality
- Maintain or improve existing test coverage

## Commit Messages

Use clear, descriptive commit messages:
- Describe what changed and why
- Reference issues if applicable
- Keep messages concise but informative

Example:
```
Add git switch command for branch switching

Implements easy git switch <branch> and easy git switch new <branch>
for faster branch navigation. Includes comprehensive tests and
documentation updates.
```

## Pull Request Process

1. Create a feature branch: `git switch -c feature/description`
2. Make your changes with clear commits
3. Write or update tests
4. Update documentation (README.md, CHANGELOG.md)
5. Run `pytest` to verify all tests pass
6. Submit PR with description of changes

## Release Process

When preparing a release:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release date
3. Create git tag: `git tag v0.X.Y`
4. Build distribution: `python -m build`

## Questions or Issues?

- Check existing issues and documentation
- Open an issue with clear description
- Join discussions for feature ideas

Thank you for contributing! 🎉
