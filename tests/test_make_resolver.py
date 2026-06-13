"""Tests for the 'make' command family (file creation)."""

import tempfile
from pathlib import Path

import pytest

from easy_terminal.commands import make
from easy_terminal.errors import ResolveError
from easy_terminal.models import ParsedCommand


class TestMakeFileResolution:
    """Test file creation command resolution."""

    def test_create_python_file(self, tmp_path):
        """Test creating a Python file with template."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            parsed = ParsedCommand(
                family="make",
                action="file",
                context=["auth", "py"],
                raw_args=["easy", "make", "file", "auth", "py"],
            )
            resolution = make.resolve(parsed)
            
            # Check resolution metadata
            assert resolution.risk is not None
            assert "auth.py" in resolution.message
            
            # Check file was created
            assert (tmp_path / "auth.py").exists()
            content = (tmp_path / "auth.py").read_text()
            assert "def main()" in content
            assert "if __name__" in content
        finally:
            os.chdir(original_cwd)

    def test_create_json_file(self, tmp_path):
        """Test creating a JSON file with template."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            parsed = ParsedCommand(
                family="make",
                action="file",
                context=["config", "json"],
                raw_args=["easy", "make", "file", "config", "json"],
            )
            resolution = make.resolve(parsed)
            
            assert (tmp_path / "config.json").exists()
            content = (tmp_path / "config.json").read_text()
            assert "{" in content
            assert "}" in content
        finally:
            os.chdir(original_cwd)

    def test_create_markdown_file(self, tmp_path):
        """Test creating a Markdown file with template."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            parsed = ParsedCommand(
                family="make",
                action="file",
                context=["README", "md"],
                raw_args=["easy", "make", "file", "README", "md"],
            )
            resolution = make.resolve(parsed)
            
            assert (tmp_path / "README.md").exists()
            content = (tmp_path / "README.md").read_text()
            assert "# README" in content
        finally:
            os.chdir(original_cwd)

    def test_missing_filename(self):
        """Test error when filename is missing."""
        parsed = ParsedCommand(
            family="make",
            action="file",
            context=["py"],
            raw_args=["easy", "make", "file", "py"],
        )
        with pytest.raises(ResolveError, match="Not enough arguments"):
            make.resolve(parsed)

    def test_missing_filetype(self):
        """Test error when filetype is missing."""
        parsed = ParsedCommand(
            family="make",
            action="file",
            context=["config"],
            raw_args=["easy", "make", "file", "config"],
        )
        with pytest.raises(ResolveError, match="Not enough arguments"):
            make.resolve(parsed)

    def test_unsupported_filetype(self):
        """Test error for unsupported file type."""
        parsed = ParsedCommand(
            family="make",
            action="file",
            context=["test", "xyz"],
            raw_args=["easy", "make", "file", "test", "xyz"],
        )
        with pytest.raises(ResolveError, match="Unknown file type"):
            make.resolve(parsed)

    def test_file_already_exists(self, tmp_path):
        """Test error when file already exists."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create file first
            (tmp_path / "existing.py").write_text("# existing")
            
            parsed = ParsedCommand(
                family="make",
                action="file",
                context=["existing", "py"],
                raw_args=["easy", "make", "file", "existing", "py"],
            )
            with pytest.raises(ResolveError, match="already exists"):
                make.resolve(parsed)
        finally:
            os.chdir(original_cwd)

    def test_filename_with_extension(self, tmp_path):
        """Test creating file when filename already includes extension."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            parsed = ParsedCommand(
                family="make",
                action="file",
                context=["config.json", "json"],
                raw_args=["easy", "make", "file", "config.json", "json"],
            )
            resolution = make.resolve(parsed)
            
            assert (tmp_path / "config.json").exists()
        finally:
            os.chdir(original_cwd)
