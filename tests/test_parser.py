from easy_terminal.parser import parse_input


def test_parse_git_commit_context():
    parsed = parse_input(["git", "commit", "game", "project", "recent"])

    assert parsed is not None
    assert parsed.family == "git"
    assert parsed.action == "commit"
    assert parsed.context == ["game", "project", "recent"]


def test_parse_open_uses_family_as_action():
    parsed = parse_input(["open", "resume", "pdf"])

    assert parsed is not None
    assert parsed.family == "open"
    assert parsed.action == "open"
    assert parsed.context == ["resume", "pdf"]


def test_parse_doc_aliases():
    parsed = parse_input(["docs"])

    assert parsed is not None
    assert parsed.family == "doc"
    assert parsed.action == "doc"


def test_parse_git_repo_actions():
    parsed = parse_input(["git", "publish", "https://github.com/Ber/Repo.git"])

    assert parsed is not None
    assert parsed.family == "git"
    assert parsed.action == "publish"
    assert parsed.context == ["https://github.com/ber/repo.git"]
    assert parsed.raw_args == ["git", "publish", "https://github.com/Ber/Repo.git"]


def test_reject_vague_assistant_request():
    assert parse_input(["please", "upload", "my", "stuff"]) is None
