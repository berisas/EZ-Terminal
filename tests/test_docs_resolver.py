from easy_terminal.models import ParsedCommand
from easy_terminal.resolver import resolve


def test_doc_resolution_prints_help_without_commands():
    parsed = ParsedCommand(family="doc", action="doc", context=[], raw_args=["doc"])

    resolution = resolve(parsed)

    assert resolution.commands == []
    assert resolution.risk == "safe"
    assert "easy git commit <context>" in resolution.message
    assert "easy find <context>" in resolution.message
