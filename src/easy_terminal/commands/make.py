"""File creation command resolver for 'easy make file' command family.

Enables intuitive file creation with intelligent template generation:
    easy make file auth py          # creates auth.py
    easy make file config json      # creates config.json
    easy make file README md        # creates README.md
"""

from __future__ import annotations

from pathlib import Path

from easy_terminal import messages
from easy_terminal.errors import ResolveError
from easy_terminal.models import ParsedCommand, Resolution
from easy_terminal.risk import MILD

# File type to extension mapping
TYPE_EXTENSIONS = {
    "py": ".py",
    "python": ".py",
    "js": ".js",
    "javascript": ".js",
    "ts": ".ts",
    "typescript": ".ts",
    "json": ".json",
    "md": ".md",
    "markdown": ".md",
    "yaml": ".yaml",
    "yml": ".yml",
    "toml": ".toml",
    "txt": ".txt",
    "text": ".txt",
    "sh": ".sh",
    "bash": ".sh",
    "html": ".html",
    "css": ".css",
    "scss": ".scss",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "h": ".h",
    "rs": ".rs",
    "rust": ".rs",
    "go": ".go",
    "rb": ".rb",
    "ruby": ".rb",
}


def resolve(parsed: ParsedCommand) -> Resolution:
    """Main dispatcher for file creation commands.

    Validates that action is 'file' and requires both filename and filetype
    in context. Generates appropriate template based on file type.

    Args:
        parsed: ParsedCommand with action='file' and context=[filename, filetype].

    Returns:
        Resolution with file creation command and template content.

    Raises:
        ResolveError: If arguments invalid or file already exists.
    """
    if parsed.action != "file":
        raise ResolveError("Unsupported make action. Try: easy make file <name> <type>")

    if len(parsed.context) < 2:
        raise ResolveError(
            "Not enough arguments. Try: easy make file <filename> <filetype>\n"
            "Example: easy make file config py"
        )

    filename = parsed.context[0]
    filetype = parsed.context[1].lower()

    if filetype not in TYPE_EXTENSIONS:
        supported = ", ".join(sorted(TYPE_EXTENSIONS.keys()))
        raise ResolveError(
            f"Unknown file type '{filetype}'.\n"
            f"Supported types: {supported}"
        )

    extension = TYPE_EXTENSIONS[filetype]
    full_filename = filename if filename.endswith(extension) else f"{filename}{extension}"
    filepath = Path.cwd() / full_filename

    if filepath.exists():
        raise ResolveError(f"File '{full_filename}' already exists.")

    content = _generate_template(filename, filetype)
    _write_file(filepath, content)

    return Resolution(
        commands=[["echo", f"Created {full_filename}"]],
        risk=MILD,
        message=f"File '{full_filename}' created successfully.",
    )


def _generate_template(filename: str, filetype: str) -> str:
    """Generate appropriate template content based on file type.

    Design rationale: Different file types benefit from different starting
    templates. Python files get docstring and main guard. JSON/YAML get
    empty objects. Markdown gets basic structure. This reduces initial setup.

    Args:
        filename: Base name of the file (without extension).
        filetype: File type identifier (e.g., 'py', 'json').

    Returns:
        Template content string suitable for the file type.
    """
    # Python module
    if filetype in {"py", "python"}:
        return f'"""Module: {filename}."""\n\n\ndef main():\n    pass\n\n\nif __name__ == "__main__":\n    main()\n'

    # JavaScript/TypeScript
    if filetype in {"js", "javascript"}:
        return f'// {filename}.js\n\nfunction main() {{\n  // TODO: Add implementation\n}}\n\nmodule.exports = {{ main }};\n'

    if filetype in {"ts", "typescript"}:
        return f'// {filename}.ts\n\nfunction main(): void {{\n  // TODO: Add implementation\n}}\n\nexport {{ main }};\n'

    # JSON
    if filetype == "json":
        return "{\n  \n}\n"

    # YAML
    if filetype in {"yaml", "yml"}:
        return f"# {filename}\n# Configuration file\n\n"

    # TOML
    if filetype == "toml":
        return f"# {filename}\n# Configuration file\n\n[project]\nname = \"{filename}\"\nversion = \"0.1.0\"\n"

    # Markdown
    if filetype in {"md", "markdown"}:
        return f"# {filename}\n\n## Overview\n\nAdd content here.\n\n## Usage\n\nAdd usage information.\n"

    # Shell script
    if filetype in {"sh", "bash"}:
        return f"#!/bin/bash\n# {filename}\n# Description of script\n\n"

    # HTML
    if filetype == "html":
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
</head>
<body>
    <h1>{filename}</h1>
</body>
</html>
"""

    # CSS
    if filetype in {"css", "scss"}:
        return f"/* {filename} */\n\nbody {{\n  /* Add styles */\n}}\n"

    # Java
    if filetype == "java":
        class_name = filename.replace("-", "_").replace(" ", "_")
        return f'public class {class_name} {{\n    public static void main(String[] args) {{\n        // TODO: Add implementation\n    }}\n}}\n'

    # Rust
    if filetype in {"rs", "rust"}:
        return f"// {filename}\n\nfn main() {{\n    println!(\"Hello from {filename}!\");\n}}\n"

    # Go
    if filetype == "go":
        return f'package main\n\nimport "fmt"\n\nfunc main() {{\n    fmt.Println("Hello from {filename}")\n}}\n'

    # Ruby
    if filetype in {"rb", "ruby"}:
        return f"#!/usr/bin/env ruby\n# {filename}\n\ndef main\n  # TODO: Add implementation\nend\n\nmain if __FILE__ == $PROGRAM_NAME\n"

    # C/C++/Header files
    if filetype in {"cpp", "c"}:
        guard = filename.upper().replace("-", "_").replace(".", "_")
        return f"// {filename}\n\n#include <stdio.h>\n\nint main() {{\n    // TODO: Add implementation\n    return 0;\n}}\n"

    if filetype == "h":
        guard = filename.upper().replace("-", "_").replace(".", "_")
        return f"#ifndef {guard}\n#define {guard}\n\n// TODO: Add content\n\n#endif // {guard}\n"

    # Default fallback for text files
    return f"# {filename}\n\n"


def _write_file(filepath: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed.

    Creates parent directories automatically to support nested file creation
    (e.g., 'easy make file src/config.py py' creates src/ if missing).

    Args:
        filepath: Path object where file will be created.
        content: Content to write to file.

    Raises:
        ResolveError: If file creation fails.
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
    except OSError as e:
        raise ResolveError(f"Failed to create file: {e}")
