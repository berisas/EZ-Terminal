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
