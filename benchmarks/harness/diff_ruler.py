"""Diff Ruler & YAGNI Code Minimalism Analyzer."""
from __future__ import annotations

import ast
import os
from typing import Any, Dict, List, Set

# Comprehensive set of Python Standard Library top-level modules
PYTHON_STDLIB_MODULES: Set[str] = {
    "__future__", "_thread", "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect", "builtins",
    "bz2", "calendar", "cmath", "cmd", "code", "codecs", "collections", "colorsys",
    "compileall", "concurrent", "configparser", "contextlib", "contextvars", "copy",
    "copyreg", "cProfile", "csv", "ctypes", "curses", "dataclasses", "datetime",
    "dbm", "decimal", "difflib", "dis", "doctest", "email", "encodings", "ensurepip",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "graphlib", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "importlib", "inspect", "io", "ipaddress",
    "itertools", "json", "keyword", "linecache", "locale", "logging", "lzma",
    "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
    "msvcrt", "multiprocessing", "netrc", "nntplib", "numbers", "operator", "optparse",
    "os", "pathlib", "pdb", "pickle", "pickletools", "pkgutil", "platform", "plistlib",
    "poplib", "posix", "pprint", "profile", "pstats", "pty", "pwd", "py_compile",
    "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select", "selectors",
    "shelve", "shlex", "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr",
    "socket", "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics",
    "string", "stringprep", "struct", "subprocess", "sunau", "symbol", "symtable",
    "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
    "termios", "test", "textwrap", "threading", "time", "timeit", "tkinter",
    "token", "tokenize", "tomllib", "trace", "traceback", "tracemalloc", "tty",
    "turtle", "turtledemo", "types", "typing", "typing_extensions", "unicodedata", "unittest", "urllib",
    "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "winreg",
    "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile",
    "zipimport", "zlib",
}


def count_executable_loc(source_code: str) -> int:
    """Count non-empty, non-comment executable lines of code."""
    count = 0
    for line in source_code.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def inspect_source_ast(source_code: str) -> Dict[str, Any]:
    """Parse source AST and compute architectural complexity metrics."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as err:
        return {
            "syntax_valid": False,
            "error": str(err),
            "classes_count": 0,
            "functions_count": 0,
            "ast_nodes_count": 0,
            "imports": [],
            "non_stdlib_imports": [],
        }

    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    total_nodes = sum(1 for _ in ast.walk(tree))

    imported_modules: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module.split(".")[0])

    # Separate stdlib from external
    non_stdlib = [mod for mod in imported_modules if mod not in PYTHON_STDLIB_MODULES and not mod.startswith(".")]

    return {
        "syntax_valid": True,
        "classes_count": len(classes),
        "functions_count": len(functions),
        "ast_nodes_count": total_nodes,
        "imports": list(set(imported_modules)),
        "non_stdlib_imports": list(set(non_stdlib)),
    }


def audit_diff_and_yagni(
    source_file_path: str,
    golden_loc: int = 35,
    max_classes: int = 1,
    require_stdlib_only: bool = True,
) -> Dict[str, Any]:
    """Audit a solution for diff size, YAGNI minimalism, and stdlib purity.

    Parameters:
        source_file_path: Path to the target implementation source file.
        golden_loc: Target minimal lines of code for the task.
        max_classes: Maximum recommended class hierarchies.
        require_stdlib_only: Whether external packages are forbidden.

    Returns:
        Structured YAGNI metrics dict.
    """
    if not os.path.exists(source_file_path):
        return {
            "file_exists": False,
            "loc": 0,
            "brevity_score": 0.0,
            "yagni_pass": False,
            "error": "File does not exist",
        }

    with open(source_file_path, "r", encoding="utf-8", errors="replace") as f:
        source_code = f.read()

    loc = count_executable_loc(source_code)
    ast_info = inspect_source_ast(source_code)

    # Brevity score: 1.0 at or below golden_loc, decreasing smoothly to 0.0 as excess lines reach +100
    excess_loc = max(0, loc - golden_loc)
    brevity_score = max(0.0, 1.0 - (excess_loc / 100.0))

    # Architecture penalties
    class_penalty = 0.0
    if ast_info["classes_count"] > max_classes:
        class_penalty = 0.2 * (ast_info["classes_count"] - max_classes)

    stdlib_penalty = 0.0
    if require_stdlib_only and len(ast_info.get("non_stdlib_imports", [])) > 0:
        stdlib_penalty = 0.5  # Heavy penalty for unneeded external dependencies

    final_score = max(0.0, brevity_score - class_penalty - stdlib_penalty)
    yagni_pass = (loc <= golden_loc * 2.5) and (len(ast_info.get("non_stdlib_imports", [])) == 0)

    return {
        "file_exists": True,
        "executable_loc": loc,
        "golden_loc": golden_loc,
        "classes_count": ast_info.get("classes_count", 0),
        "functions_count": ast_info.get("functions_count", 0),
        "ast_nodes_count": ast_info.get("ast_nodes_count", 0),
        "imports": ast_info.get("imports", []),
        "non_stdlib_imports": ast_info.get("non_stdlib_imports", []),
        "is_stdlib_pure": len(ast_info.get("non_stdlib_imports", [])) == 0,
        "brevity_score": round(final_score, 4),
        "yagni_pass": yagni_pass,
    }
