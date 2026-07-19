"""Deterministic regression tests for profiler accounting and sandbox configuration."""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
import profile  # noqa: E402
import sandbox  # noqa: E402


class ProfileTests(unittest.TestCase):
    def test_extract_code_uses_last_fenced_block(self) -> None:
        self.assertEqual(profile.extract_code("```python\na = 1\n```\n```\nb = 2\n```"), "b = 2")

    def test_rate_counts_errors_in_the_denominator(self) -> None:
        rows = [
            {"outcome": "pass", "prompt_tokens": 10},
            {"outcome": "fail", "prompt_tokens": 10},
            {"outcome": "api_error", "prompt_tokens": None},
        ]
        self.assertEqual(profile._rate(rows), " 33% (1/3, errors=1)")

    def test_sandbox_requires_a_digest_pinned_image(self) -> None:
        with patch.dict(os.environ, {sandbox.IMAGE_ENV: "python:3.12-alpine"}, clear=True):
            with self.assertRaises(sandbox.SandboxUnavailable):
                sandbox._image_reference()


if __name__ == "__main__":
    unittest.main()
