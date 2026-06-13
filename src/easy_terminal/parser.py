from __future__ import annotations

from easy_terminal.models import ParsedCommand

SUPPORTED = {
    "doc": {"doc"},
    "docs": {"doc"},
    "help": {"doc"},
    "git": {
        "status", "commit", "push", "init", "remote", "repo", "publish",
        "branch", "switch", "merge", "rebase", "pull", "log", "diff",
        "reset", "revert", "restore", "clean", "show"
    },
    "python": {"run"},
    "open": {"open"},
    "find": {"find"},
    "make": {"file"},
}


def parse_input(args: list[str]) -> ParsedCommand | None:
    if not args:
        return None

    family = args[0].lower()
    if family not in SUPPORTED:
        return None

    if family in {"doc", "docs", "help"}:
        return ParsedCommand(
            family="doc",
            action="doc",
            context=_clean_context(args[1:]),
            raw_args=args,
        )

    if family in {"open", "find"}:
        return ParsedCommand(
            family=family,
            action=family,
            context=_clean_context(args[1:]),
            raw_args=args,
        )

    if len(args) < 2:
        return None

    action = args[1].lower()
    if action not in SUPPORTED[family]:
        return None

    return ParsedCommand(
        family=family,
        action=action,
        context=_clean_context(args[2:]),
        raw_args=args,
    )


def _clean_context(words: list[str]) -> list[str]:
    return [word.strip().lower() for word in words if word.strip()]
