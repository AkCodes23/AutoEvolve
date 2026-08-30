"""Tests for file_processor — including path traversal attack vectors."""
from __future__ import annotations

import os
import tempfile
import textwrap

import pytest

from benchmarks.scenarios.s7_security.src.file_processor import (
    list_files,
    process_file,
    read_file,
)


@pytest.fixture
def sample_dir():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        os.makedirs(data_dir)
        with open(os.path.join(data_dir, "hello.txt"), "w") as f:
            f.write("hello world\nline two\n")
        with open(os.path.join(data_dir, "config.ini"), "w") as f:
            f.write("[section]\nkey=value\n")
        # Create a file OUTSIDE the allowed directory
        with open(os.path.join(tmp, "secret.txt"), "w") as f:
            f.write("TOP SECRET DATA")
        yield data_dir


class TestReadFile:
    def test_read_valid_file(self, sample_dir):
        content = read_file(sample_dir, "hello.txt")
        assert "hello world" in content

    def test_read_nonexistent_file(self, sample_dir):
        with pytest.raises(FileNotFoundError):
            read_file(sample_dir, "nonexistent.txt")

    def test_traversal_dot_dot_slash(self, sample_dir):
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            read_file(sample_dir, "../secret.txt")

    def test_traversal_absolute_path(self, sample_dir):
        if os.name == "nt":
            malicious = "C:\\Windows\\System32\\drivers\\etc\\hosts"
        else:
            malicious = "/etc/passwd"
        with pytest.raises((ValueError, FileNotFoundError)):
            read_file(sample_dir, malicious)

    def test_traversal_double_dot_encoded(self, sample_dir):
        with pytest.raises((ValueError, FileNotFoundError)):
            read_file(sample_dir, "..%2F..%2Fsecret.txt")

    def test_traversal_backslash_windows(self, sample_dir):
        with pytest.raises((ValueError, FileNotFoundError)):
            read_file(sample_dir, "..\\..\\secret.txt")

    def test_traversal_null_byte(self, sample_dir):
        with pytest.raises((ValueError, FileNotFoundError, OSError)):
            read_file(sample_dir, "hello.txt\x00../secret.txt")


class TestListFiles:
    def test_list_valid_dir(self, sample_dir):
        files = list_files(sample_dir)
        assert "hello.txt" in files
        assert "config.ini" in files

    def test_does_not_list_parent_files(self, sample_dir):
        files = list_files(sample_dir)
        assert "secret.txt" not in files


class TestProcessFile:
    def test_process_valid_file(self, sample_dir):
        result = process_file(sample_dir, "hello.txt")
        assert result["filename"] == "hello.txt"
        assert result["line_count"] == 2
        assert result["word_count"] == 4
        assert result["size_bytes"] > 0

    def test_process_traversal_blocked(self, sample_dir):
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            process_file(sample_dir, "../secret.txt")


class TestSourceCodeSecurity:
    """AST-level checks on the source code itself."""

    def test_no_eval_in_source(self):
        import ast
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "file_processor.py"
        )
        with open(src_path, "r") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    pytest.fail(f"Unsafe {func.id}() found at line {node.lineno}")

    def test_no_shell_true_in_source(self):
        import ast
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "file_processor.py"
        )
        with open(src_path, "r") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        pytest.fail(f"shell=True found at line {node.lineno}")
