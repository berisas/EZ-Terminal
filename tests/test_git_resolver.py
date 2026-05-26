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
