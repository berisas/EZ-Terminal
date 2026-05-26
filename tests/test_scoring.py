from easy_terminal.scanner import candidate_from_path
from easy_terminal.scoring import rank_candidates, score_candidate


def test_scores_filename_context_recency_and_git_change(tmp_path):
    target = tmp_path / "src" / "game_project.py"
    target.parent.mkdir()
    target.write_text("print('hi')", encoding="utf-8")
    candidate = candidate_from_path(target, tmp_path, is_git_changed=True)

    score = score_candidate(candidate, ["game", "project", "recent"], extension=".py")

    assert score >= 12


def test_rank_prefers_more_specific_filename(tmp_path):
    voice = tmp_path / "voice_server.py"
    generic = tmp_path / "server.py"
    voice.write_text("print('voice')", encoding="utf-8")
    generic.write_text("print('server')", encoding="utf-8")

    ranked = rank_candidates(
        [
            candidate_from_path(generic, tmp_path),
            candidate_from_path(voice, tmp_path),
        ],
        ["voice", "server"],
        extension=".py",
        prefer_entry_files=True,
    )

    assert ranked[0][0].filename == "voice_server.py"
