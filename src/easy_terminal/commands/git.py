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
    """Main dispatcher router for git command actions.
    
    Handles routing of parsed git commands to action-specific resolvers.
    Uses early-return pattern for clarity and to avoid nested conditionals.
    Each action is resolved independently, allowing for isolated testing and
    future extension without affecting other handlers.
    
    Args:
        parsed: Validated ParsedCommand with action and context.
        
    Returns:
        Resolution object containing git commands to execute, risk level,
        and user-facing message.
        
    Raises:
        ResolveError: For unsupported git actions.
    """
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

    if parsed.action == "branch":
        return _resolve_branch(parsed)

    if parsed.action == "switch":
        return _resolve_switch(parsed)

    if parsed.action == "merge":
        return _resolve_merge(parsed)

    if parsed.action == "rebase":
        return _resolve_rebase(parsed)

    if parsed.action == "pull":
        return _resolve_pull(parsed)

    if parsed.action == "log":
        return _resolve_log(parsed)

    if parsed.action == "diff":
        return _resolve_diff(parsed)

    if parsed.action == "reset":
        return _resolve_reset(parsed)

    if parsed.action == "revert":
        return _resolve_revert(parsed)

    if parsed.action == "restore":
        return _resolve_restore(parsed)

    if parsed.action == "clean":
        return _resolve_clean(parsed)

    if parsed.action == "show":
        return _resolve_show(parsed)

    raise ResolveError("Unsupported Git action.")


def _resolve_repo(parsed: ParsedCommand) -> Resolution:
    """Query repository metadata with a four-command composite inspection.
    
    Provides a comprehensive read-only snapshot of repository state by running:
    1. Repository root detection (cross-platform, handles symlinks)
    2. Current branch name (for context-aware operations)
    3. Remote configuration (confirms origin and tracking remotes)
    4. Short status with branch tracking info (delta ahead/behind)
    
    Design rationale: Running all four together reduces round-trip costs compared
    to individual queries. All commands are read-only (SAFE risk level) and suitable
    for integration into shell prompts or status bars.
    
    Args:
        parsed: ParsedCommand (context unused for repo inspection).
        
    Returns:
        Resolution with four read-only inspection commands.
    """
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
    """Configure or inspect git remote origin.
    
    Implements smart remote configuration: if a URL is provided in context,
    adds or updates the origin remote. Otherwise, displays current remotes.
    
    URL detection strategy: Matches common git URL patterns (http://, https://,
    git@, .git suffix) to extract explicit URLs from fuzzy context. This allows
    commands like 'easy git remote github.com/user/repo.git' to work intuitively.
    
    Design choice: Uses idempotent set-url if origin exists (safe re-run),
    vs. add if missing. Avoids error handling for duplicate remotes.
    
    Args:
        parsed: ParsedCommand with context containing optional URL.
        
    Returns:
        Resolution with either remote list query or configuration command.
    """
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
    """Orchestrate repository publication workflow: standardize branch and push upstream.
    
    Implements opinionated GitHub-style publishing workflow:
    1. Rename current branch to 'main' (idempotent via -M flag)
    2. Configure origin remote if URL provided
    3. Push with -u flag to establish upstream tracking
    
    Design rationale: Handles common GitHub workflow (new repo -> GitHub -> push)
    and supports GitHub-first workflows (existing GitHub repo -> git clone -> easy publish).
    Fails fast if neither URL provided nor origin already configured, preventing
    failed pushes that would require debugging.
    
    Trade-off: Forces 'main' naming (not configurable) to match GitHub defaults
    and reduce user decision fatigue for simple publish use case.
    
    Args:
        parsed: ParsedCommand with optional URL in context.
        
    Returns:
        Resolution with sequence of commands to enable and push to main.
        
    Raises:
        ResolveError: If no origin configured and no URL provided.
    """
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
    """Resolve partial or full commit with intelligent file selection and message generation.
    
    Core algorithm for intelligent commit resolution:
    1. Parse context to detect explicit message flags (-m, --message, msg)
    2. Query git status for changed files (new, modified, deleted)
    3. If 'all' in context or single file changed, commit all changes
    4. Otherwise, score changed files against user context keywords
    5. Select top-scoring files (with score variance threshold)
    6. Generate commit message from selected filenames + context
    
    Score filtering strategy: Accepts files within 2 points of top score AND
    with score >= 3. This balances precision (only high-confidence files) with
    recall (doesn't exclude related files that scored similarly).
    
    Design choice: Generates message only from selected files' keywords if context
    is ambiguous (e.g., 'easy git commit update'). Allows natural commit messages
    without explicit -m flag in simple cases.
    
    Args:
        parsed: ParsedCommand with optional context and explicit message.
        
    Returns:
        Resolution with git add + git commit commands.
        
    Raises:
        ResolveError: If no changes found, too many ambiguous files, or status fails.
    """
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
    """Commit all changes in current working directory with message generation.
    
    Specialized resolver for 'all' keyword, targeting folder-scoped operations.
    Uses git add . (current directory only, not git add -A) to support monorepos
    where user wants to commit only their folder's changes.
    
    Message generation strategy:
    - If explicit -m flag provided: use verbatim message
    - Otherwise: filter context with LOW_SIGNAL_WORDS to remove noise
    - Build subject from first 5 meaningful words (e.g., 'Add tests' not 'Add stuff')
    - Prefix with action (Update for modifications, implicit Add detection on files)
    
    LOW_SIGNAL_WORDS design: Blocks generic words (change, file, work, today, all)
    that add no semantic value to commit messages. Prevents commits like
    'Update change' in favor of 'Update tests'.
    
    Args:
        parsed: ParsedCommand with optional explicit message.
        
    Returns:
        Resolution with git add . and git commit commands.
        
    Raises:
        ResolveError: If current directory has no changes (partial repo safety).
    """
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


def _resolve_branch(parsed: ParsedCommand) -> Resolution:
    """Resolve branch management operations.
    
    Supports operations: list, copy, delete, rename, merged, unmerged, log.
    Detects operation from context keywords; allows filler words between
    command and action (e.g., 'git branch show list' -> list).
    
    Args:
        parsed: ParsedCommand with context containing branch operation.
        
    Returns:
        Resolution with appropriate git branch command.
        
    Raises:
        ResolveError: For unsupported branch operations or missing arguments.
    """
    context = parsed.context
    
    if any(word in context for word in ["list", "show"]):
        return Resolution(
            commands=[["git", "branch", "-a"]],
            risk=SAFE,
            message="Branches listed.",
        )
    
    if "log" in context:
        if len(context) > 1:
            branch = _extract_one_arg(context, "log")
            return Resolution(
                commands=[["git", "log", branch, "--oneline"]],
                risk=SAFE,
                message=f"Commits on '{branch}' displayed.",
            )
        else:
            return Resolution(
                commands=[["git", "log", "--oneline", "-10"]],
                risk=SAFE,
                message="Last 10 commits displayed.",
            )
    
    if "copy" in context:
        old_branch, new_branch = _extract_two_args(context, "copy")
        return Resolution(
            commands=[["git", "branch", "-c", old_branch, new_branch]],
            risk=MILD,
            message=f"Branch '{old_branch}' copied to '{new_branch}'.",
        )
    
    if "delete" in context:
        if "force" in context or any(word.lower() == "force" for word in parsed.raw_args):
            branch = _extract_one_arg(context, "delete")
            return Resolution(
                commands=[["git", "branch", "-D", branch]],
                risk=MILD,
                message=f"Branch '{branch}' force deleted.",
            )
        else:
            branch = _extract_one_arg(context, "delete")
            return Resolution(
                commands=[["git", "branch", "-d", branch]],
                risk=MILD,
                message=f"Branch '{branch}' deleted.",
            )
    
    if "rename" in context or "move" in context:
        old_branch, new_branch = _extract_two_args(context, "rename")
        return Resolution(
            commands=[["git", "branch", "-m", old_branch, new_branch]],
            risk=MILD,
            message=f"Branch '{old_branch}' renamed to '{new_branch}'.",
        )
    
    if "merged" in context:
        return Resolution(
            commands=[["git", "branch", "--merged"]],
            risk=SAFE,
            message="Merged branches listed.",
        )
    
    if "unmerged" in context or "no-merged" in context or "no_merged" in context:
        return Resolution(
            commands=[["git", "branch", "--no-merged"]],
            risk=SAFE,
            message="Unmerged branches listed.",
        )
    
    raise ResolveError("Unsupported branch operation. Try: list, copy, delete, rename, merged, unmerged, log.")


def _resolve_switch(parsed: ParsedCommand) -> Resolution:
    """Resolve branch switching and creation.
    
    Detects 'new' keyword to create and switch to new branch in one command.
    Otherwise switches to existing branch.
    
    Args:
        parsed: ParsedCommand with context containing branch name.
        
    Returns:
        Resolution with git switch command (or git branch + git switch).
        
    Raises:
        ResolveError: If no branch name provided.
    """
    if not parsed.context:
        raise ResolveError("Branch name required. Try: easy git switch <branch-name>")
    
    if "new" in parsed.context:
        branch = _extract_one_arg(parsed.context, "new")
        return Resolution(
            commands=[["git", "switch", "-c", branch]],
            risk=MILD,
            message=f"Created and switched to branch '{branch}'.",
        )
    else:
        branch = parsed.context[0]
        return Resolution(
            commands=[["git", "switch", branch]],
            risk=SAFE,
            message=f"Switched to branch '{branch}'.",
        )


def _resolve_merge(parsed: ParsedCommand) -> Resolution:
    """Resolve merge operations.
    
    Supports: standard merge, no-ff (merge commit), squash.
    
    Args:
        parsed: ParsedCommand with merge operation and branch name.
        
    Returns:
        Resolution with git merge command.
        
    Raises:
        ResolveError: If no branch name provided.
    """
    if not parsed.context:
        raise ResolveError("Branch name required. Try: easy git merge <branch-name>")
    
    if "squash" in parsed.context:
        branch = _extract_one_arg(parsed.context, "squash")
        return Resolution(
            commands=[["git", "merge", "--squash", branch]],
            risk=MILD,
            message=f"Squash merge from '{branch}' ready for commit.",
        )
    
    if any(word in parsed.context for word in ["no-ff", "no_ff", "nooff"]):
        branch = _extract_one_arg(parsed.context, "no-ff")
        return Resolution(
            commands=[["git", "merge", "--no-ff", branch]],
            risk=MILD,
            message=f"Merge commit created from '{branch}'.",
        )
    
    branch = parsed.context[0]
    return Resolution(
        commands=[["git", "merge", branch]],
        risk=MILD,
        message=f"Merged '{branch}' into current branch.",
    )


def _resolve_rebase(parsed: ParsedCommand) -> Resolution:
    """Resolve rebase operations.
    
    Supports: standard rebase, interactive, continue, abort.
    
    Args:
        parsed: ParsedCommand with rebase operation and optional branch/flags.
        
    Returns:
        Resolution with git rebase command.
        
    Raises:
        ResolveError: For invalid rebase operations.
    """
    if not parsed.context:
        raise ResolveError("Rebase operation required. Try: easy git rebase <branch>")
    
    if any(word in parsed.context for word in ["continue"]):
        return Resolution(
            commands=[["git", "rebase", "--continue"]],
            risk=MILD,
            message="Rebase continued.",
        )
    
    if any(word in parsed.context for word in ["abort"]):
        return Resolution(
            commands=[["git", "rebase", "--abort"]],
            risk=SAFE,
            message="Rebase aborted.",
        )
    
    if any(word in parsed.context for word in ["interactive", "interact"]):
        branch = _extract_one_arg(parsed.context, "interactive")
        return Resolution(
            commands=[["git", "rebase", "-i", branch]],
            risk=MILD,
            message=f"Interactive rebase with '{branch}' started.",
        )
    
    branch = parsed.context[0]
    return Resolution(
        commands=[["git", "rebase", branch]],
        risk=MILD,
        message=f"Rebased current branch onto '{branch}'.",
    )


def _resolve_pull(parsed: ParsedCommand) -> Resolution:
    """Resolve pull operations.
    
    Supports: standard pull, pull with rebase.
    
    Args:
        parsed: ParsedCommand with optional rebase flag.
        
    Returns:
        Resolution with git pull command.
    """
    if any(word in parsed.context for word in ["rebase", "rbse"]):
        return Resolution(
            commands=[["git", "pull", "--rebase"]],
            risk=SAFE,
            message="Pulled with rebase (cleaner history).",
        )
    
    return Resolution(
        commands=[["git", "pull"]],
        risk=SAFE,
        message="Pulled latest changes.",
    )


def _resolve_log(parsed: ParsedCommand) -> Resolution:
    """Resolve log inspection operations.
    
    Supports: standard log, last n commits, visual graph, diffs, branch-specific.
    
    Args:
        parsed: ParsedCommand with log operation and optional count/branch.
        
    Returns:
        Resolution with git log command.
        
    Raises:
        ResolveError: For invalid log operations.
    """
    if any(word in parsed.context for word in ["graph", "visual"]):
        return Resolution(
            commands=[["git", "log", "--graph", "--oneline", "--all"]],
            risk=SAFE,
            message="Visual branch history displayed.",
        )
    
    if any(word in parsed.context for word in ["diff"]):
        return Resolution(
            commands=[["git", "log", "-p"]],
            risk=SAFE,
            message="Commit diffs displayed.",
        )
    
    if "past" in parsed.context:
        try:
            count_idx = parsed.context.index("past") + 1
            if count_idx < len(parsed.context):
                count_str = parsed.context[count_idx]
                count = int(count_str) if count_str.isdigit() else 10
            else:
                count = 10
        except (ValueError, IndexError):
            count = 10
        return Resolution(
            commands=[["git", "log", f"-{count}", "--oneline"]],
            risk=SAFE,
            message=f"Last {count} commits displayed.",
        )
    
    if "branch" in parsed.context and len(parsed.context) > 1:
        branch = _extract_one_arg(parsed.context, "branch")
        return Resolution(
            commands=[["git", "log", branch, "--oneline"]],
            risk=SAFE,
            message=f"Commits on '{branch}' displayed.",
        )
    
    return Resolution(
        commands=[["git", "log", "--oneline", "-10"]],
        risk=SAFE,
        message="Last 10 commits displayed.",
    )


def _resolve_diff(parsed: ParsedCommand) -> Resolution:
    """Resolve diff inspection operations.
    
    Supports: unstaged changes, staged changes, comparison with branch/commit.
    
    Args:
        parsed: ParsedCommand with optional diff context (staged, branch, commit).
        
    Returns:
        Resolution with git diff command.
    """
    if any(word in parsed.context for word in ["staged", "cached", "indexed"]):
        return Resolution(
            commands=[["git", "diff", "--staged"]],
            risk=SAFE,
            message="Staged changes displayed.",
        )
    
    if parsed.context and parsed.context[0] not in {"diff"}:
        target = parsed.context[0]
        return Resolution(
            commands=[["git", "diff", target]],
            risk=SAFE,
            message=f"Changes vs '{target}' displayed.",
        )
    
    return Resolution(
        commands=[["git", "diff"]],
        risk=SAFE,
        message="Unstaged changes displayed.",
    )


def _resolve_reset(parsed: ParsedCommand) -> Resolution:
    """Resolve file unstaging operations.
    
    Args:
        parsed: ParsedCommand with file path.
        
    Returns:
        Resolution with git reset command.
        
    Raises:
        ResolveError: If no file specified.
    """
    if not parsed.context:
        raise ResolveError("File name required. Try: easy git reset <file>")
    
    file_path = parsed.context[0]
    return Resolution(
        commands=[["git", "reset", file_path]],
        risk=MILD,
        message=f"File '{file_path}' unstaged.",
    )


def _resolve_revert(parsed: ParsedCommand) -> Resolution:
    """Resolve revert operations (create new commit undoing changes).
    
    Args:
        parsed: ParsedCommand with commit hash/ref.
        
    Returns:
        Resolution with git revert command.
        
    Raises:
        ResolveError: If no commit specified.
    """
    if not parsed.context:
        raise ResolveError("Commit reference required. Try: easy git revert <commit>")
    
    commit = parsed.context[0]
    return Resolution(
        commands=[["git", "revert", commit]],
        risk=MILD,
        message=f"Revert of '{commit}' started.",
    )


def _resolve_restore(parsed: ParsedCommand) -> Resolution:
    """Resolve file restoration operations (discard working tree changes).
    
    Args:
        parsed: ParsedCommand with file path.
        
    Returns:
        Resolution with git restore command.
        
    Raises:
        ResolveError: If no file specified.
    """
    if not parsed.context:
        raise ResolveError("File name required. Try: easy git restore <file>")
    
    file_path = parsed.context[0]
    return Resolution(
        commands=[["git", "restore", file_path]],
        risk=MILD,
        message=f"File '{file_path}' restored to last commit.",
    )


def _resolve_clean(parsed: ParsedCommand) -> Resolution:
    """Resolve cleanup operations (remove untracked files).
    
    Args:
        parsed: ParsedCommand (looks for 'untracked' keyword).
        
    Returns:
        Resolution with git clean command.
    """
    return Resolution(
        commands=[["git", "clean", "-fd"]],
        risk=MILD,
        message="Untracked files and directories removed.",
    )


def _resolve_show(parsed: ParsedCommand) -> Resolution:
    """Resolve show operations (display specific commit details).
    
    Args:
        parsed: ParsedCommand with commit hash/ref.
        
    Returns:
        Resolution with git show command.
        
    Raises:
        ResolveError: If no commit specified.
    """
    if not parsed.context:
        raise ResolveError("Commit reference required. Try: easy git show <commit>")
    
    commit = parsed.context[0]
    return Resolution(
        commands=[["git", "show", commit]],
        risk=SAFE,
        message=f"Commit '{commit}' details displayed.",
    )


def _repo_root() -> Path:
    """Detect and return the root directory of the git repository.
    
    Uses git rev-parse --show-toplevel for reliable cross-platform detection
    (handles Windows drive letters, symlinks, and mountpoints correctly).
    Preferred over manual .git directory searching, which breaks with worktrees.
    
    Calls .resolve() to normalize symlinks and relative paths to absolute form,
    ensuring consistent path comparisons for relative_to() operations.
    
    Returns:
        Path object pointing to repository root (absolute, normalized).
        
    Raises:
        ResolveError: If current directory is not inside a git repository.
    """
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
    """Check whether origin remote is configured.
    
    Uses git remote get-url (returns 0 if remote exists, 1 if missing).
    Simpler and more portable than parsing 'git remote -v' output or checking
    git config directly.
    
    Returns:
        True if origin remote exists and is accessible, False otherwise.
    """
    completed = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _current_branch() -> str:
    """Retrieve the name of the currently checked-out branch.
    
    Uses git branch --show-current (available in git >= 2.22).
    Returns empty string on detached HEAD, which we treat as error
    (push -u requires a branch name).
    
    Alternative: git rev-parse --abbrev-ref HEAD returns 'HEAD' on detached
    state; current approach is more explicit about constraint.
    
    Returns:
        Current branch name (non-empty string).
        
    Raises:
        ResolveError: On detached HEAD or git failure.
    """
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
    """Check if current working directory has any git changes.
    
    Uses git status --short -- . to scope status to current directory only.
    This respects directory boundaries (monorepo safety): running from src/
    doesn't include changes from tests/ folder.
    
    The -- . separator is critical for safety: without it, . is treated as
    a file path argument, not directory scope specifier.
    
    Returns:
        True if any changes (new, modified, deleted files) in current directory.
    """
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
    """Extract first valid git remote URL from context words.
    
    Pattern matching strategy:
    - Detect HTTPS/HTTP URLs: explicit protocol (most common from web UIs)
    - Detect SSH URLs: git@ prefix (GitHub/GitLab SSH format)
    - Detect bare paths ending in .git: supports shorthand 'easy git remote
      github.com/user/repo.git' without protocol
    
    First match returned (left-to-right); assumes user provides only one URL
    in context. Doesn't validate URL format (git will fail at execution time
    if invalid, providing clear feedback).
    
    Args:
        context: List of user-provided words from command context.
        
    Returns:
        First valid URL pattern found, or None if no URL in context.
    """
    for word in context:
        if word.startswith("http://") or word.startswith("https://") or word.startswith("git@"):
            return word
        if word.endswith(".git"):
            return word
    return None


def _action_tail(parsed: ParsedCommand) -> list[str]:
    """Extract context words following the git action.
    
    Format: easy git <action> [context...]
    - raw_args[0] = 'easy'
    - raw_args[1] = 'git'
    - raw_args[2:] = action and context words
    
    Returns:
        Unparsed words after 'git' command (includes action + context).
    """
    return parsed.raw_args[2:]


def _context_without_message(parsed: ParsedCommand) -> list[str]:
    """Extract context words, excluding anything after explicit message marker.
    
    Detects -m/-m-message/message/msg flags and truncates context at that point.
    Allows separation of user intent (context) from explicit message override.
    
    Example:
        Input: 'easy git commit tests added -m "Fix bug"'
        Returns: ['tests', 'added']
    
    This enables both implicit message generation (from context) and
    explicit override (from -m flag) in same resolver.
    
    Returns:
        Lowercase context words before message marker, or full context if no marker.
    """
    marker_index = _message_marker_index(_action_tail(parsed))
    if marker_index is None:
        return parsed.context
    return [word.lower() for word in _action_tail(parsed)[:marker_index]]


def _explicit_commit_message(parsed: ParsedCommand) -> str | None:
    """Extract user-provided commit message after -m flag, if present.
    
    Parses text after marker (e.g., -m) as explicit message override.
    Validates that message is non-empty (fails fast if user writes
    'easy git commit file -m' with no text).
    
    Returns:
        User message string (may contain spaces), or None if no marker found.
        
    Raises:
        ResolveError: If marker present but no text after it.
    """
    tail = _action_tail(parsed)
    marker_index = _message_marker_index(tail)
    if marker_index is None:
        return None

    message = " ".join(tail[marker_index + 1 :]).strip()
    if not message:
        raise ResolveError("Commit message marker found, but no message was provided.")
    return message


def _message_marker_index(words: list[str]) -> int | None:
    """Find index of message marker token in word list.
    
    Accepts multiple conventions:
    - POSIX standard: -m (git style)
    - Long form: --message (GNU style)
    - Natural language: 'message' or 'msg' (user-friendly)
    
    Case-insensitive to catch 'Message' or 'MSG' variants.
    Returns first occurrence; ignores duplicates (left-associative).
    
    Returns:
        Index of marker word, or None if no marker found.
    """
    for index, word in enumerate(words):
        if word.lower() in {"-m", "--message", "message", "msg"}:
            return index
    return None


def _changed_files(root: Path) -> list[FileCandidate]:
    """Parse git status output and build ranked candidate file list.
    
    Algorithm:
    1. Run 'git status --short' to list all changes (modified, staged, new, deleted)
    2. Parse two-character status codes (XY format: staging area + working tree)
    3. Extract file paths (handles git rename format: old -> new)
    4. For regular files: create candidate with git_changed=True flag
    5. For new untracked directories (??): scan recursively and add all files
    
    Design rationale: Untracked directories treated as high-intent signals
    (developer likely wants all files in that dir committed together).
    Modified/staged files treated individually.
    
    Note: Deleted files included in candidates for completeness, though
    commit typically stages them implicitly via git add -A.
    
    Args:
        root: Repository root for resolving relative paths.
        
    Returns:
        List of FileCandidate objects for changed files (may be empty).
        
    Raises:
        ResolveError: If git status command fails.
    """
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
    """Extract file path from git status --short line.
    
    Format: XY <path>
    - X, Y: status codes (1 char each, position 0-1)
    - [space]: separator (position 2)
    - Path starts at position 3
    
    Special case: git rename format shows 'old -> new'.
    Extract 'new' path (right side), which is the current file name.
    
    Git wraps paths with quotes if they contain special characters;
    strip quotes for internal path handling.
    
    Args:
        line: Single line from 'git status --short' output.
        
    Returns:
        Unwrapped, normalized file path.
    """
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip('"')


def _select_commit_files(
    candidates: list[FileCandidate],
    context: list[str],
) -> list[FileCandidate]:
    """Use fuzzy ranking to select files matching user context.
    
    Selection strategy (conservative to minimize false positives):
    1. Single changed file: auto-select (no ambiguity)
    2. Multiple files: rank against context using scoring module
    3. Filter: keep files within 2 points of top score AND score >= 3
    4. If filtered set non-empty: return it
    5. Otherwise: fail with helpful error suggesting more context
    
    Score thresholds tuned empirically:
    - gap <= 2: catches synonym/related files (e.g., test_file.py + file.py)
    - score >= 3: rejects marginal matches from generic keywords
    
    Rationale: Rather than auto-guess files, we fail and ask for clarification.
    This prevents accidental commits of unintended files (safety-first design).
    
    Args:
        candidates: List of changed files.
        context: User-provided keywords for ranking.
        
    Returns:
        Non-empty list of selected FileCandidate objects.
        
    Raises:
        ResolveError: If ranking fails or no files meet threshold (prompts
        user to provide more specific context).
    """
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
    """Generate natural commit message from file metadata and user context.
    
    Message template: '<action> <subject>'
    
    Action heuristic:
    - All files untracked (new): "Add"
    - Otherwise: "Update" (covers modifications, deletions, mixed)
    
    Subject generation priority:
    1. Use filtered context (remove LOW_SIGNAL_WORDS noise)
    2. If context empty & single file: extract from file.keywords (e.g., "auth"
       from "auth.py")
    3. Fallback: "files" (generic)
    
    File extension filter: Exclude language tags (py, txt, md) from keywords
    to avoid subjects like "Update py" instead of "Update auth".
    
    Limit to 5 words to keep messages concise and readable.
    
    Examples:
    - 'Add auth service' (new file + meaningful context)
    - 'Update tests' (modified file, low-signal words filtered)
    - 'Update files' (ambiguous context)
    
    Args:
        candidates: Selected files for commit.
        context: User context words (pre-filtered of message marker).
        
    Returns:
        Generated commit message string.
    """
    action = "Update"
    if all(_is_untracked(candidate) for candidate in candidates):
        action = "Add"

    useful_words = [word for word in context if word not in LOW_SIGNAL_WORDS]
    if not useful_words and len(candidates) == 1:
        useful_words = [word for word in candidates[0].keywords if word not in {"py", "txt", "md"}]

    subject = " ".join(_format_word(word) for word in useful_words[:5]) or "files"
    return f"{action} {subject}"


def _is_untracked(candidate: FileCandidate) -> bool:
    """Check if file is untracked (new to repository).
    
    Uses git status --short on individual file. Returns true if status
    code is "??" (both working tree and index untracked).
    
    Used to choose commit action ("Add" for new files, "Update" for
    modified/deleted). This heuristic improves message clarity.
    
    Args:
        candidate: FileCandidate object with path.
        
    Returns:
        True if file is untracked (status ??), False otherwise.
    """
    completed = subprocess.run(
        ["git", "status", "--short", "--", str(candidate.path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.startswith("??")


def _relative_paths(candidates: list[FileCandidate], root: Path) -> list[str]:
    """Convert absolute file paths to relative form with ./ prefix.
    
    Produces git-friendly paths suitable for 'git add' command:
    - Relative to repository root (required by git add)
    - Normalized to POSIX forward slashes (cross-platform)
    - Prefixed with ./ for clarity (distinguishes from git refs)
    
    Example: /repo/src/auth.py -> ./src/auth.py
    
    Args:
        candidates: FileCandidate objects (have .path attribute).
        root: Repository root path (must be absolute/resolved).
        
    Returns:
        List of relative path strings ready for git add.
    """
    paths = []
    for candidate in candidates:
        relative = candidate.path.resolve().relative_to(root)
        paths.append("./" + relative.as_posix())
    return paths


def _format_word(word: str) -> str:
    """Apply display formatting rules to keywords.
    
    Currently: Uppercase acronyms (AI -> AI).
    Designed as extension point for acronym/domain-specific formatting.
    
    Rationale: Improves readability of generated messages:
    - "Add AI features" (formatted) vs "Add ai features" (raw)
    
    Args:
        word: Lowercase keyword from context or filename.
        
    Returns:
        Formatted word (typically uppercased for acronyms, otherwise unchanged).
    """
    if word == "ai":
        return "AI"
    return word


def _too_many_changed(candidates: list[FileCandidate]) -> str:
    """Format error message for ambiguous multi-file commit.
    
    Shows first 5 changed files (truncated to avoid overwhelming output)
    and suggests user provide more context words to disambiguate.
    
    Design: Helps user understand why commit failed and what to do next,
    maintaining learning loop for fuzzy command system.
    
    Args:
        candidates: All changed files (may be 100s in large changes).
        
    Returns:
        User-facing error message string.
    """
    shown = "\n".join(
        f"{index}. ./{candidate.path.name}"
        for index, candidate in enumerate(candidates[:5], 1)
    )
    return f"Too many changed files:\n{shown}\n\nTry: easy git commit <more specific words>"


def _extract_one_arg(context: list[str], marker: str) -> str:
    """Extract single argument from context following a marker word.
    
    Example: context=['copy', 'old_name', 'new_name'] + marker='copy'
    Returns the next word after 'copy'.
    
    Args:
        context: List of context words.
        marker: Keyword to find and extract argument after.
        
    Returns:
        The word following the marker.
        
    Raises:
        ResolveError: If marker not found or no argument after marker.
    """
    if marker not in context:
        raise ResolveError(f"Marker '{marker}' not found in context.")
    
    marker_idx = context.index(marker)
    if marker_idx + 1 >= len(context):
        raise ResolveError(f"No argument provided after '{marker}'.")
    
    return context[marker_idx + 1]


def _extract_two_args(context: list[str], marker: str) -> tuple[str, str]:
    """Extract two arguments from context following a marker word.
    
    Example: context=['copy', 'old_name', 'new_name'] + marker='copy'
    Returns ('old_name', 'new_name').
    
    Args:
        context: List of context words.
        marker: Keyword to find and extract arguments after.
        
    Returns:
        Tuple of (first_arg, second_arg).
        
    Raises:
        ResolveError: If not enough arguments provided.
    """
    if marker not in context:
        raise ResolveError(f"Marker '{marker}' not found in context.")
    
    marker_idx = context.index(marker)
    if marker_idx + 2 >= len(context):
        raise ResolveError(f"Need two arguments after '{marker}', but got {len(context) - marker_idx - 1}.")
    
    return context[marker_idx + 1], context[marker_idx + 2]

