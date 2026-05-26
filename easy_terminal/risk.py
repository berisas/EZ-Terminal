from __future__ import annotations

SAFE = "safe"
MILD = "mild"
RISKY = "risky"
DANGEROUS = "dangerous"


def classify(command: list[str]) -> str:
    lowered = [part.lower() for part in command]
    joined = " ".join(lowered)

    if "rm -rf" in joined or "format" in lowered or "sudo" in lowered:
        return DANGEROUS

    if lowered[:2] in (["git", "add"], ["git", "commit"]):
        return MILD

    if lowered[:2] in (["git", "reset"], ["pip", "install"], ["npm", "install"]):
        return RISKY

    return SAFE
