"""Calibration tests for the caller reporter.

The failure this guards against is the one it already had once: `find_callers` skipped the file a
symbol was defined in, so every same-module call site was invisible, and the tool then announced
"no references found" and suggested the symbol might be dead code. That is worse than silence,
because it argues for a deletion that would break the three callers sitting ten lines below. A
mechanism whose whole value is that you can trust its output needs its output pinned.
"""
from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import callers  # noqa: E402


class Sandbox:
    """A throwaway directory holding named .py files, for one test."""

    def __init__(self, files: dict[str, str]) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for name, source in files.items():
            path = os.path.join(self.root, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(textwrap.dedent(source))

    def __enter__(self) -> Sandbox:
        return self

    def __exit__(self, *exc: object) -> None:
        self.tmp.cleanup()

    def symbols(self, name: str) -> dict:
        found = {}
        for symbol, line in callers.defined_symbols(os.path.join(self.root, name)):
            found[symbol] = {"file": name, "line": line}
        return found

    def hits(self, name: str) -> dict:
        return callers.find_callers(self.root, self.symbols(name),
                                    callers.python_files(self.root))


class DefinedSymbolTests(unittest.TestCase):
    def test_finds_functions_classes_and_public_methods(self) -> None:
        with Sandbox({"api.py": '''
            def fetch_rows(query):
                pass

            class Catalog:
                def lookup(self, sku):
                    pass

                def _private(self):
                    pass
        '''}) as box:
            self.assertEqual(set(box.symbols("api.py")), {"fetch_rows", "Catalog", "lookup"})

    def test_skips_names_too_common_to_be_useful(self) -> None:
        with Sandbox({"api.py": "def main():\n    pass\n\ndef run():\n    pass\n"}) as box:
            self.assertEqual(box.symbols("api.py"), {})

    def test_a_syntax_error_yields_nothing_rather_than_raising(self) -> None:
        with Sandbox({"broken.py": "def fetch_rows(:\n"}) as box:
            self.assertEqual(callers.defined_symbols(os.path.join(box.root, "broken.py")), [])


class CallSiteTests(unittest.TestCase):
    def test_reports_callers_inside_the_defining_file(self) -> None:
        """The regression that made this file exist: same-module callers were all invisible."""
        with Sandbox({"api.py": '''
            def fetch_rows(query):
                return []

            def summarize(query):
                return len(fetch_rows(query))
        '''}) as box:
            sites = box.hits("api.py")["fetch_rows"]
            self.assertTrue(any(kind == "call" for _, _, kind, _ in sites))

    def test_does_not_report_the_definition_line_as_a_call(self) -> None:
        with Sandbox({"api.py": "def fetch_rows(query):\n    return []\n"}) as box:
            self.assertEqual(box.hits("api.py")["fetch_rows"], [])

    def test_separates_real_calls_from_prose_mentions(self) -> None:
        with Sandbox({
            "api.py": "def fetch_rows(query):\n    return []\n",
            "worker.py": '''
                """Runs fetch_rows on a schedule."""
                from api import fetch_rows

                def nightly(query):
                    return fetch_rows(query)
            ''',
        }) as box:
            kinds = [kind for _, _, kind, _ in box.hits("api.py")["fetch_rows"]]
            self.assertIn("call", kinds)
            self.assertIn("text", kinds)

    def test_a_substring_of_another_name_is_not_a_call(self) -> None:
        with Sandbox({
            "api.py": "def fetch(query):\n    return []\n",
            "worker.py": "def go(q):\n    return prefetch_all(q)\n",
        }) as box:
            self.assertEqual(box.hits("api.py")["fetch"], [])


class CorpusTests(unittest.TestCase):
    def test_walk_prunes_vendored_and_cache_directories(self) -> None:
        with Sandbox({
            "api.py": "def fetch_rows(q):\n    return []\n",
            "node_modules/pkg/thing.py": "fetch_rows(1)\n",
            "__pycache__/stale.py": "fetch_rows(2)\n",
        }) as box:
            scanned = {os.path.basename(p) for p in callers.python_files(box.root)}
            self.assertEqual(scanned, {"api.py"})


if __name__ == "__main__":
    unittest.main()
