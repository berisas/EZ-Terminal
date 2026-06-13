from pathlib import Path

from easy_terminal.commands import git
from easy_terminal.models import ParsedCommand
from easy_terminal.scanner import candidate_from_path


def test_git_commit_resolves_add_and_message(tmp_path, monkeypatch):
    target = tmp_path / "game_project.py"
    target.write_text("print('game')", encoding="utf-8")
    candidate = candidate_from_path(target, tmp_path, is_git_changed=True)
    parsed = ParsedCommand(
        family="git",
        action="commit",
        context=["game", "project", "recent"],
        raw_args=["git", "commit", "game", "project", "recent"],
    )

    monkeypatch.setattr(git, "_repo_root", lambda: Path(tmp_path))
    monkeypatch.setattr(git, "_changed_files", lambda root: [candidate])
    monkeypatch.setattr(git, "_is_untracked", lambda item: True)

    resolution = git.resolve(parsed)

    assert resolution.commands == [
        ["git", "add", "./game_project.py"],
        ["git", "commit", "-m", "Add game project"],
    ]
    assert resolution.risk == "mild"


def test_git_remote_sets_existing_origin(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="remote",
        context=["https://github.com/berisas/ez-terminal.git"],
        raw_args=["git", "remote", "https://github.com/berisas/EZ-Terminal.git"],
    )
    monkeypatch.setattr(git, "_has_origin", lambda: True)

    resolution = git.resolve(parsed)

    assert resolution.commands == [
        ["git", "remote", "set-url", "origin", "https://github.com/berisas/EZ-Terminal.git"]
    ]
    assert resolution.risk == "mild"


def test_git_publish_adds_origin_and_pushes_first(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="publish",
        context=["https://github.com/berisas/ez-terminal.git"],
        raw_args=["git", "publish", "https://github.com/berisas/EZ-Terminal.git"],
    )
    monkeypatch.setattr(git, "_has_origin", lambda: False)

    resolution = git.resolve(parsed)

    assert resolution.commands == [
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", "https://github.com/berisas/EZ-Terminal.git"],
        ["git", "push", "-u", "origin", "main"],
    ]
    assert resolution.risk == "mild"


def test_git_repo_check_reports_repository_context():
    parsed = ParsedCommand(
        family="git",
        action="repo",
        context=["check"],
        raw_args=["git", "repo", "check"],
    )

    resolution = git.resolve(parsed)

    assert ["git", "rev-parse", "--show-toplevel"] in resolution.commands
    assert ["git", "remote", "-v"] in resolution.commands


def test_git_push_first_uses_current_branch(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="push",
        context=["first"],
        raw_args=["git", "push", "first"],
    )
    monkeypatch.setattr(git, "_current_branch", lambda: "master")

    resolution = git.resolve(parsed)

    assert resolution.commands == [["git", "push", "-u", "origin", "master"]]


def test_git_commit_all_stages_current_folder(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="commit",
        context=["all"],
        raw_args=["git", "commit", "all"],
    )
    monkeypatch.setattr(git, "_repo_root", lambda: Path("C:/repo"))
    monkeypatch.setattr(git, "_has_changes_in_current_path", lambda: True)

    resolution = git.resolve(parsed)

    assert resolution.commands == [
        ["git", "add", "."],
        ["git", "commit", "-m", "Update current folder"],
    ]
    assert resolution.risk == "mild"


def test_git_commit_all_uses_extra_words_for_message(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="commit",
        context=["all", "easy", "terminal"],
        raw_args=["git", "commit", "all", "easy", "terminal"],
    )
    monkeypatch.setattr(git, "_repo_root", lambda: Path("C:/repo"))
    monkeypatch.setattr(git, "_has_changes_in_current_path", lambda: True)

    resolution = git.resolve(parsed)

    assert resolution.commands[1] == ["git", "commit", "-m", "Update easy terminal"]


def test_git_commit_all_uses_explicit_message(monkeypatch):
    parsed = ParsedCommand(
        family="git",
        action="commit",
        context=["all", "-m", "add", "first", "version"],
        raw_args=["git", "commit", "all", "-m", "Add first version"],
    )
    monkeypatch.setattr(git, "_repo_root", lambda: Path("C:/repo"))
    monkeypatch.setattr(git, "_has_changes_in_current_path", lambda: True)

    resolution = git.resolve(parsed)

    assert resolution.commands[1] == ["git", "commit", "-m", "Add first version"]


def test_git_commit_fuzzy_uses_explicit_message(tmp_path, monkeypatch):
    target = tmp_path / "game_project.py"
    target.write_text("print('game')", encoding="utf-8")
    candidate = candidate_from_path(target, tmp_path, is_git_changed=True)
    parsed = ParsedCommand(
        family="git",
        action="commit",
        context=["game", "message", "add", "arcade", "mode"],
        raw_args=["git", "commit", "game", "message", "Add arcade mode"],
    )

    monkeypatch.setattr(git, "_repo_root", lambda: Path(tmp_path))
    monkeypatch.setattr(git, "_changed_files", lambda root: [candidate])

    resolution = git.resolve(parsed)

    assert resolution.commands == [
        ["git", "add", "./game_project.py"],
        ["git", "commit", "-m", "Add arcade mode"],
    ]


# Branch management tests
def test_git_branch_list():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["list"],
        raw_args=["git", "branch", "list"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "-a"]]
    assert resolution.risk == "safe"


def test_git_branch_copy():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["copy", "main", "feature"],
        raw_args=["git", "branch", "copy", "main", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "-c", "main", "feature"]]
    assert resolution.risk == "mild"


def test_git_branch_delete():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["delete", "feature"],
        raw_args=["git", "branch", "delete", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "-d", "feature"]]
    assert resolution.risk == "mild"


def test_git_branch_force_delete():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["delete", "feature", "force"],
        raw_args=["git", "branch", "delete", "feature", "force"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "-D", "feature"]]
    assert resolution.risk == "mild"


def test_git_branch_rename():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["rename", "old-name", "new-name"],
        raw_args=["git", "branch", "rename", "old-name", "new-name"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "-m", "old-name", "new-name"]]
    assert resolution.risk == "mild"


def test_git_branch_merged():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["merged"],
        raw_args=["git", "branch", "merged"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "--merged"]]
    assert resolution.risk == "safe"


def test_git_branch_unmerged():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["unmerged"],
        raw_args=["git", "branch", "unmerged"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "branch", "--no-merged"]]
    assert resolution.risk == "safe"


def test_git_branch_log():
    parsed = ParsedCommand(
        family="git",
        action="branch",
        context=["log", "main"],
        raw_args=["git", "branch", "log", "main"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "log", "main", "--oneline"]]
    assert resolution.risk == "safe"


# Switch tests
def test_git_switch_to_branch():
    parsed = ParsedCommand(
        family="git",
        action="switch",
        context=["feature"],
        raw_args=["git", "switch", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "switch", "feature"]]
    assert resolution.risk == "safe"


def test_git_switch_create_new_branch():
    parsed = ParsedCommand(
        family="git",
        action="switch",
        context=["new", "feature"],
        raw_args=["git", "switch", "new", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "switch", "-c", "feature"]]
    assert resolution.risk == "mild"


# Merge tests
def test_git_merge_standard():
    parsed = ParsedCommand(
        family="git",
        action="merge",
        context=["feature"],
        raw_args=["git", "merge", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "merge", "feature"]]
    assert resolution.risk == "mild"


def test_git_merge_no_ff():
    parsed = ParsedCommand(
        family="git",
        action="merge",
        context=["no-ff", "feature"],
        raw_args=["git", "merge", "no-ff", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "merge", "--no-ff", "feature"]]
    assert resolution.risk == "mild"


def test_git_merge_squash():
    parsed = ParsedCommand(
        family="git",
        action="merge",
        context=["squash", "feature"],
        raw_args=["git", "merge", "squash", "feature"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "merge", "--squash", "feature"]]
    assert resolution.risk == "mild"


# Rebase tests
def test_git_rebase_standard():
    parsed = ParsedCommand(
        family="git",
        action="rebase",
        context=["main"],
        raw_args=["git", "rebase", "main"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "rebase", "main"]]
    assert resolution.risk == "mild"


def test_git_rebase_interactive():
    parsed = ParsedCommand(
        family="git",
        action="rebase",
        context=["interactive", "main"],
        raw_args=["git", "rebase", "interactive", "main"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "rebase", "-i", "main"]]
    assert resolution.risk == "mild"


def test_git_rebase_continue():
    parsed = ParsedCommand(
        family="git",
        action="rebase",
        context=["continue"],
        raw_args=["git", "rebase", "continue"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "rebase", "--continue"]]
    assert resolution.risk == "mild"


def test_git_rebase_abort():
    parsed = ParsedCommand(
        family="git",
        action="rebase",
        context=["abort"],
        raw_args=["git", "rebase", "abort"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "rebase", "--abort"]]
    assert resolution.risk == "safe"


# Pull tests
def test_git_pull_standard():
    parsed = ParsedCommand(
        family="git",
        action="pull",
        context=[],
        raw_args=["git", "pull"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "pull"]]
    assert resolution.risk == "safe"


def test_git_pull_rebase():
    parsed = ParsedCommand(
        family="git",
        action="pull",
        context=["rebase"],
        raw_args=["git", "pull", "rebase"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "pull", "--rebase"]]
    assert resolution.risk == "safe"


# Log tests
def test_git_log_standard():
    parsed = ParsedCommand(
        family="git",
        action="log",
        context=[],
        raw_args=["git", "log"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "log", "--oneline", "-10"]]
    assert resolution.risk == "safe"


def test_git_log_graph():
    parsed = ParsedCommand(
        family="git",
        action="log",
        context=["graph"],
        raw_args=["git", "log", "graph"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "log", "--graph", "--oneline", "--all"]]
    assert resolution.risk == "safe"


def test_git_log_past():
    parsed = ParsedCommand(
        family="git",
        action="log",
        context=["past", "20"],
        raw_args=["git", "log", "past", "20"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "log", "-20", "--oneline"]]
    assert resolution.risk == "safe"


def test_git_log_diff():
    parsed = ParsedCommand(
        family="git",
        action="log",
        context=["diff"],
        raw_args=["git", "log", "diff"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "log", "-p"]]
    assert resolution.risk == "safe"


# Diff tests
def test_git_diff_unstaged():
    parsed = ParsedCommand(
        family="git",
        action="diff",
        context=[],
        raw_args=["git", "diff"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "diff"]]
    assert resolution.risk == "safe"


def test_git_diff_staged():
    parsed = ParsedCommand(
        family="git",
        action="diff",
        context=["staged"],
        raw_args=["git", "diff", "staged"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "diff", "--staged"]]
    assert resolution.risk == "safe"


def test_git_diff_branch():
    parsed = ParsedCommand(
        family="git",
        action="diff",
        context=["main"],
        raw_args=["git", "diff", "main"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "diff", "main"]]
    assert resolution.risk == "safe"


# Reset tests
def test_git_reset():
    parsed = ParsedCommand(
        family="git",
        action="reset",
        context=["file.py"],
        raw_args=["git", "reset", "file.py"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "reset", "file.py"]]
    assert resolution.risk == "mild"


# Revert tests
def test_git_revert():
    parsed = ParsedCommand(
        family="git",
        action="revert",
        context=["abc123"],
        raw_args=["git", "revert", "abc123"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "revert", "abc123"]]
    assert resolution.risk == "mild"


# Restore tests
def test_git_restore():
    parsed = ParsedCommand(
        family="git",
        action="restore",
        context=["file.py"],
        raw_args=["git", "restore", "file.py"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "restore", "file.py"]]
    assert resolution.risk == "mild"


# Clean tests
def test_git_clean_untracked():
    parsed = ParsedCommand(
        family="git",
        action="clean",
        context=["untracked"],
        raw_args=["git", "clean", "untracked"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "clean", "-fd"]]
    assert resolution.risk == "mild"


# Show tests
def test_git_show_commit():
    parsed = ParsedCommand(
        family="git",
        action="show",
        context=["abc123"],
        raw_args=["git", "show", "abc123"],
    )
    resolution = git.resolve(parsed)
    assert resolution.commands == [["git", "show", "abc123"]]
    assert resolution.risk == "safe"


