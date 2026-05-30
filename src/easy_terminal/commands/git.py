from __future__ import annotations

import subprocess
from pathlib import Path

from easy_terminal import messages
from easy_terminal.errors import ResolveError
from easy_terminal.models import FileCandidate, ParsedCommand, Resolution
from easy_terminal.risk import MILD, SAFE
from easy_terminal.scanner import candidate_from_path, scan_files
from easy_terminal.scoring import rank_candidates

LOW_SIGNAL_WORDS = {
    "change",
    "changes",
    "stuff",
    "file",
    "files",
    "work",
    "recent",
    "recently",
    "new",
    "newest",
    "latest",
    "today",
    "all",
}


def resolve(parsed: ParsedCommand) -> Resolution:
    if parsed.action == "init":
        return Resolution(
            commands=[["git", "init"]],
            risk=MILD,
            message="Repository initialized.",
        )

    if parsed.action == "status":
        return Resolution(
            commands=[["git", "status", "--short"]],
            risk=SAFE,
            message=messages.pick(messages.GIT_STATUS),
        )

    if parsed.action == "push":
        if set(parsed.context) & {"first", "upstream", "main"}:
            branch = _current_branch()
            return Resolution(
                commands=[["git", "push", "-u", "origin", branch]],
                risk=SAFE,
                message=messages.pick(messages.GIT_PUSH),
            )
        return Resolution(
            commands=[["git", "push"]],
            risk=SAFE,
            message=messages.pick(messages.GIT_PUSH),
        )

    if parsed.action == "repo":
        return _resolve_repo(parsed)

    if parsed.action == "remote":
        return _resolve_remote(parsed)

    if parsed.action == "publish":
        return _resolve_publish(parsed)

    if parsed.action == "commit":
        return _resolve_commit(parsed)

    raise ResolveError("Unsupported Git action.")


def _resolve_repo(parsed: ParsedCommand) -> Resolution:
    return Resolution(
        commands=[
            ["git", "rev-parse", "--show-toplevel"],
            ["git", "branch", "--show-current"],
            ["git", "remote", "-v"],
            ["git", "status", "--short", "--branch"],
        ],
        risk=SAFE,
        message="Repository context checked.",
    )


def _resolve_remote(parsed: ParsedCommand) -> Resolution:
    url = _remote_url(_action_tail(parsed))
    if not url:
        return Resolution(
            commands=[["git", "remote", "-v"]],
            risk=SAFE,
            message="Remote configuration checked.",
        )

    if _has_origin():
        command = ["git", "remote", "set-url", "origin", url]
    else:
        command = ["git", "remote", "add", "origin", url]

    return Resolution(
        commands=[command],
        risk=MILD,
        message="Origin remote configured.",
    )


def _resolve_publish(parsed: ParsedCommand) -> Resolution:
    url = _remote_url(_action_tail(parsed))
    commands = [["git", "branch", "-M", "main"]]

    if url:
        if _has_origin():
            commands.append(["git", "remote", "set-url", "origin", url])
        else:
            commands.append(["git", "remote", "add", "origin", url])
    elif not _has_origin():
        raise ResolveError(
            "No origin remote. Try: easy git publish https://github.com/user/repo.git"
        )

    commands.append(["git", "push", "-u", "origin", "main"])
    return Resolution(
        commands=commands,
        risk=MILD,
        message="Repository published.",
    )


def _resolve_commit(parsed: ParsedCommand) -> Resolution:
    root = _repo_root()
    context = _context_without_message(parsed)
    explicit_message = _explicit_commit_message(parsed)
    if "all" in context:
        return _resolve_commit_all(parsed)

    changed = _changed_files(root)
    if not changed:
        raise ResolveError("There is nothing to commit.")

    selected = _select_commit_files(changed, context)
    message = explicit_message or _commit_message(selected, context)
    commands = [["git", "add", *_relative_paths(selected, root)], ["git", "commit", "-m", message]]

    return Resolution(commands=commands, risk=MILD, message=messages.pick(messages.GIT_COMMIT))


def _resolve_commit_all(parsed: ParsedCommand) -> Resolution:
    if not _has_changes_in_current_path():
        raise ResolveError("There is nothing to commit in this folder.")

    explicit_message = _explicit_commit_message(parsed)
    if explicit_message:
        message = explicit_message
    else:
        useful_words = [
            word for word in _context_without_message(parsed) if word not in LOW_SIGNAL_WORDS
        ]
        subject = " ".join(_format_word(word) for word in useful_words[:5]) or "current folder"
        message = f"Update {subject}"

    return Resolution(
        commands=[["git", "add", "."], ["git", "commit", "-m", message]],
        risk=MILD,
        message=messages.pick(messages.GIT_COMMIT),
    )


def _repo_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ResolveError("Current directory is not inside a Git repository.")
    return Path(completed.stdout.strip()).resolve()


def _has_origin() -> bool:
    completed = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _current_branch() -> str:
    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    branch = completed.stdout.strip()
    if completed.returncode != 0 or not branch:
        raise ResolveError("Could not detect the current branch.")
    return branch


def _has_changes_in_current_path() -> bool:
    completed = subprocess.run(
        ["git", "status", "--short", "--", "."],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ResolveError("Git status failed.")
    return bool(completed.stdout.strip())


def _remote_url(context: list[str]) -> str | None:
    for word in context:
        if word.startswith("http://") or word.startswith("https://") or word.startswith("git@"):
            return word
        if word.endswith(".git"):
            return word
    return None


def _action_tail(parsed: ParsedCommand) -> list[str]:
    return parsed.raw_args[2:]


def _context_without_message(parsed: ParsedCommand) -> list[str]:
    marker_index = _message_marker_index(_action_tail(parsed))
    if marker_index is None:
        return parsed.context
    return [word.lower() for word in _action_tail(parsed)[:marker_index]]


def _explicit_commit_message(parsed: ParsedCommand) -> str | None:
    tail = _action_tail(parsed)
    marker_index = _message_marker_index(tail)
    if marker_index is None:
        return None

    message = " ".join(tail[marker_index + 1 :]).strip()
    if not message:
        raise ResolveError("Commit message marker found, but no message was provided.")
    return message


def _message_marker_index(words: list[str]) -> int | None:
    for index, word in enumerate(words):
        if word.lower() in {"-m", "--message", "message", "msg"}:
            return index
    return None


def _changed_files(root: Path) -> list[FileCandidate]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ResolveError("Could not read changed files from Git status.")

    candidates: list[FileCandidate] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        relative_path = _status_path(line)
        path = root / relative_path
        if path.exists() and path.is_file():
            candidates.append(candidate_from_path(path, root, is_git_changed=True))
        elif path.exists() and path.is_dir() and line.startswith("??"):
            for candidate in scan_files(path):
                candidates.append(candidate_from_path(candidate.path, root, is_git_changed=True))
    return candidates


def _status_path(line: str) -> str:
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def _select_commit_files(
    candidates: list[FileCandidate],
    context: list[str],
) -> list[FileCandidate]:
    if len(candidates) == 1:
        return candidates

    ranked = rank_candidates(candidates, context)
    if not ranked:
        raise ResolveError(_too_many_changed(candidates))

    top_score = ranked[0][1]
    selected = [candidate for candidate, score in ranked if top_score - score <= 2 and score >= 3]
    if selected:
        return selected

    raise ResolveError(_too_many_changed(candidates))


def _commit_message(candidates: list[FileCandidate], context: list[str]) -> str:
    action = "Update"
    if all(_is_untracked(candidate) for candidate in candidates):
        action = "Add"

    useful_words = [word for word in context if word not in LOW_SIGNAL_WORDS]
    if not useful_words and len(candidates) == 1:
        useful_words = [word for word in candidates[0].keywords if word not in {"py", "txt", "md"}]

    subject = " ".join(_format_word(word) for word in useful_words[:5]) or "files"
    return f"{action} {subject}"


def _is_untracked(candidate: FileCandidate) -> bool:
    completed = subprocess.run(
        ["git", "status", "--short", "--", str(candidate.path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.startswith("??")


def _relative_paths(candidates: list[FileCandidate], root: Path) -> list[str]:
    paths = []
    for candidate in candidates:
        relative = candidate.path.resolve().relative_to(root)
        paths.append("./" + relative.as_posix())
    return paths


def _format_word(word: str) -> str:
    if word == "ai":
        return "AI"
    return word


def _too_many_changed(candidates: list[FileCandidate]) -> str:
    shown = "\n".join(
        f"{index}. ./{candidate.path.name}"
        for index, candidate in enumerate(candidates[:5], 1)
    )
    return f"Too many changed files:\n{shown}\n\nTry: easy git commit <more specific words>"
