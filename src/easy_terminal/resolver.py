from __future__ import annotations

from easy_terminal.commands import docs
from easy_terminal.commands import find as find_command
from easy_terminal.commands import git, make, open_file, python
from easy_terminal.errors import ResolveError
from easy_terminal.models import ParsedCommand, Resolution


def resolve(parsed: ParsedCommand) -> Resolution:
    if parsed.family == "doc":
        return docs.resolve(parsed)
    if parsed.family == "git":
        return git.resolve(parsed)
    if parsed.family == "python":
        return python.resolve(parsed)
    if parsed.family == "open":
        return open_file.resolve(parsed)
    if parsed.family == "find":
        return find_command.resolve(parsed)
    if parsed.family == "make":
        return make.resolve(parsed)

    raise ResolveError("not a command. try starting with doc, git, python, open, find, or make.")
