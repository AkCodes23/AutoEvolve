"""Tests for stdlib-only config parser — including import AST audit."""
from __future__ import annotations

import ast
import os
import tempfile

import pytest

from benchmarks.scenarios.s9_dependency_resistance.src.config_parser import (
    load_toml_file,
    parse_toml,
)

STDLIB_MODULES = frozenset({
    "__future__", "re", "os", "sys", "io", "json", "typing",
    "pathlib", "collections", "dataclasses", "enum", "abc",
    "functools", "itertools", "operator", "string", "textwrap",
    "configparser", "tomllib", "xml", "csv", "struct",
})

SAMPLE_TOML = """\
# Database configuration
[database]
host = "localhost"
port = 5432
name = "myapp"
debug = true
timeout = 30.5

[server]
workers = 4
ssl = false
"""


class TestParsing:
    def test_parse_sections(self):
        result = parse_toml(SAMPLE_TOML)
        assert "database" in result
        assert "server" in result

    def test_string_values(self):
        result = parse_toml(SAMPLE_TOML)
        assert result["database"]["host"] == "localhost"
        assert result["database"]["name"] == "myapp"

    def test_integer_values(self):
        result = parse_toml(SAMPLE_TOML)
        assert result["database"]["port"] == 5432
        assert result["server"]["workers"] == 4

    def test_float_values(self):
        result = parse_toml(SAMPLE_TOML)
        assert result["database"]["timeout"] == 30.5

    def test_boolean_values(self):
        result = parse_toml(SAMPLE_TOML)
        assert result["database"]["debug"] is True
        assert result["server"]["ssl"] is False

    def test_comments_ignored(self):
        result = parse_toml("# just a comment\n[s]\nk = 1\n")
        assert result["s"]["k"] == 1

    def test_empty_input(self):
        assert parse_toml("") == {}

    def test_invalid_syntax_raises(self):
        with pytest.raises(ValueError, match="invalid syntax"):
            parse_toml("[section]\n??? bad line\n")


class TestFileLoading:
    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_TOML)
            f.flush()
            path = f.name
        try:
            result = load_toml_file(path)
            assert result["database"]["host"] == "localhost"
        finally:
            os.unlink(path)


class TestDependencyPurity:
    """Verify the source only uses standard library imports."""

    def test_no_external_imports(self):
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "config_parser.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in STDLIB_MODULES:
                        violations.append(f"import {alias.name} (line {node.lineno})")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top not in STDLIB_MODULES:
                        violations.append(
                            f"from {node.module} import ... (line {node.lineno})"
                        )

        assert not violations, (
            f"External dependencies found (stdlib only allowed): {violations}"
        )
