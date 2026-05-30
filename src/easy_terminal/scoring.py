from __future__ import annotations

from datetime import datetime, timedelta

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - exercised only without optional dependency
    fuzz = None

from easy_terminal.models import FileCandidate

RECENT_WORDS = {"recent", "recently", "new", "newest", "latest", "today"}
COMMON_ENTRY_FILES = {"main.py", "app.py", "server.py", "run.py"}

EXTENSION_ALIASES = {
    "python": ".py",
    "py": ".py",
    "pdf": ".pdf",
    "doc": ".doc",
    "docx": ".docx",
    "word": ".docx",
    "image": ".png",
    "images": ".png",
    "picture": ".jpg",
    "pictures": ".jpg",
    "video": ".mp4",
    "videos": ".mp4",
    "zip": ".zip",
    "archive": ".zip",
    "text": ".txt",
    "txt": ".txt",
}


def rank_candidates(
    candidates: list[FileCandidate],
    context: list[str],
    extension: str | None = None,
    prefer_entry_files: bool = False,
) -> list[tuple[FileCandidate, int]]:
    scored = [
        (candidate, score_candidate(candidate, context, extension, prefer_entry_files))
        for candidate in candidates
    ]
    return sorted(
        [(candidate, score) for candidate, score in scored if score > 0],
        key=lambda item: (item[1], item[0].modified_time),
        reverse=True,
    )


def score_candidate(
    candidate: FileCandidate,
    context: list[str],
    extension: str | None = None,
    prefer_entry_files: bool = False,
) -> int:
    words = [word.lower() for word in context]
    filename_words = set(candidate.keywords)
    folder_text = " ".join(candidate.folder_names)
    filename_text = candidate.filename.lower()
    score = 0

    if extension and candidate.extension == extension:
        score += 2

    for word in words:
        wanted_extension = EXTENSION_ALIASES.get(word)
        if wanted_extension and candidate.extension == wanted_extension:
            score += 2

        if word in filename_words or word in filename_text:
            score += 3
            continue

        if word in folder_text:
            score += 2
            continue

        if _weak_match(word, filename_words):
            score += 1

    if any(word in RECENT_WORDS for word in words):
        if candidate.modified_time >= datetime.now() - timedelta(days=2):
            score += 2
        if candidate.created_time >= datetime.now() - timedelta(days=2):
            score += 2

    if candidate.is_git_changed:
        score += 2

    if prefer_entry_files and candidate.filename.lower() in COMMON_ENTRY_FILES:
        score += 1

    return score


def is_ambiguous(ranked: list[tuple[FileCandidate, int]]) -> bool:
    if len(ranked) < 2:
        return False
    top_score = ranked[0][1]
    second_score = ranked[1][1]
    return top_score == second_score or top_score - second_score <= 1


def _weak_match(word: str, candidates: set[str]) -> bool:
    if len(word) < 3:
        return False

    for candidate in candidates:
        if len(candidate) < 3:
            continue
        if word in candidate or candidate in word:
            return True
        if fuzz and fuzz.ratio(word, candidate) >= 75:
            return True

    return False
