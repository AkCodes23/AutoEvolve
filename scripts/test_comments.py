"""Calibration tests for the comment-noise reporter.

The point of this file is the FALSE POSITIVE half. A reporter that flags a comment recording a
measured result is worse than no reporter: it trains you to skim past the output, and the
comments it would have you delete are the most expensive text in a repository. So every
detector is pinned twice, once on text it must flag and once on text it must not, and the
must-not cases are taken verbatim from this repository's own source.
"""
from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comments  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_source(source: str) -> list[tuple[int, str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(textwrap.dedent(source))
        return comments.scan(path)


def tiers(source: str) -> list[str]:
    return [tier for _, tier, _ in scan_source(source)]


class CommentedOutCodeTests(unittest.TestCase):
    def test_flags_disabled_statements(self) -> None:
        for body in ["import json", "x = compute(1)", "print(user)", "self.cache = {}",
                     "return None", "for row in rows:\n    pass", "del cache[key]",
                     "raise ValueError('nope')", "result += 1", "await fetch(url)"]:
            self.assertTrue(comments.is_commented_out_code(body), body)

    def test_does_not_flag_prose(self) -> None:
        prose = [
            "Fix at the root rather than patching each call site",
            "import the module before you read the config",
            "global state is rebuilt on every run",
            "for each row, check the total",
            "return the count, or None when the catalog is empty",
            "delete this once the migration lands",
            "raise the cap only after measuring",
            "See build_adapters.py for the generated form",
            "python3 scripts/callers.py --rev HEAD~3",
            "e.g. parse_tags(\"a, b\") drops the empty entry",
            "TODO", "ok", "noqa", "n", "why",
            # A bare annotation is how a quoted sentence sneaks past the parser. This exact line
            # was a live false positive against a grader in the retired eval suite.
            'ponytail: "One guard in the shared function is a smaller diff than a guard in each"',
            "Note: the caller already holds the lock",
            "Invariant: every kept experiment is a commit",
        ]
        for body in prose:
            self.assertFalse(comments.is_commented_out_code(body), body)

    def test_an_annotation_that_assigns_is_still_code(self) -> None:
        self.assertTrue(comments.is_commented_out_code("retries: int = 3"))

    def test_a_space_before_the_paren_means_prose(self) -> None:
        """locale.py:1641 lists `# Quechua (Peru)`, which parses as a call. PEP 8 forbids f (x)."""
        for prose in ["Quechua (Peru)", "Romanian (Romania)", "normalize (see the RFC)"]:
            self.assertFalse(comments.is_commented_out_code(prose), prose)
        self.assertTrue(comments.is_commented_out_code("normalize(key)"))

    def test_a_bare_call_beside_live_code_is_an_annotation(self) -> None:
        """statistics.py:1260 records where a magic constant came from, in a trailing comment."""
        self.assertFalse(comments.is_commented_out_code("sqrt(1 / sys.float_info.max)",
                                                        trailing=True))
        self.assertTrue(comments.is_commented_out_code("sqrt(1 / sys.float_info.max)"))
        self.assertEqual(tiers("scale = 2.0 ** -512  # sqrt(1 / sys.float_info.max)\n"), [])

    def test_an_assignment_beside_live_code_is_still_suspicious(self) -> None:
        self.assertTrue(comments.is_commented_out_code("cache = {}", trailing=True))


class DividerTests(unittest.TestCase):
    def test_flags_a_bare_rule(self) -> None:
        for body in ["=" * 40, "-------------", "****", "# # # #"]:
            self.assertTrue(comments.is_divider(body), body)

    def test_does_not_flag_sentences_containing_dashes(self) -> None:
        for body in ["a - b is negative when b wins", "step 1 -> step 2", "--rev is optional"]:
            self.assertFalse(comments.is_divider(body), body)

    def test_a_banner_with_words_is_judged_on_the_words(self) -> None:
        """Decoration around a real section name must not fail a commit over punctuation."""
        self.assertFalse(comments.is_divider("--- 4. regression canary: ledger row shape ---"))
        self.assertEqual(comments.undecorate("--- 4. regression canary ---"), "4. regression canary")
        self.assertEqual(tiers("""
            # --- 4. regression canary: ledger row shape ---------------------------
            rows = build_ledger(order)
        """), [])

    def test_decoration_does_not_hide_commented_out_code(self) -> None:
        self.assertEqual([t for t in tiers("""
            # ---- cache = {} ----
            value = 1
        """)], ["noise"])


class VacuousDocstringTests(unittest.TestCase):
    def test_flags_a_docstring_rebuilt_from_the_signature(self) -> None:
        self.assertEqual(tiers('''
            def get_user_name(user):
                """Get the user name."""
                return user.name
        '''), ["noise"])

    def test_keeps_a_docstring_that_adds_information(self) -> None:
        self.assertEqual(tiers('''
            def median_of(samples):
                """An outlier moves a mean, not a median, so noisy signals use the middle."""
                return sorted(samples)[len(samples) // 2]
        '''), [])

    def test_keeps_a_multiline_docstring(self) -> None:
        self.assertEqual(tiers('''
            def get_user(user):
                """Get the user.

                Longer text is left alone: the summary line is a convention, not noise.
                """
                return user
        '''), [])


class RestatementTests(unittest.TestCase):
    def test_flags_a_comment_restating_the_next_line(self) -> None:
        self.assertEqual(tiers("""
            # increment the counter
            counter = counter + 1
        """), ["candidate"])

    def test_flags_a_trailing_comment_restating_its_own_line(self) -> None:
        self.assertEqual(tiers("""
            total = sum(items)  # sum the items
        """), ["candidate"])

    def test_keeps_a_comment_that_records_a_why(self) -> None:
        self.assertEqual(tiers("""
            # A single slow run is the machine, not the change, so take the middle value.
            ordered = sorted(samples)
        """), [])


class ExemptionTests(unittest.TestCase):
    def test_a_decorated_work_marker_survives_undecoration(self) -> None:
        """KEEP_PREFIXES is checked after undecorate(), so the two must compose.

        `evolve:` is the load-bearing one. AGENTS.md, SKILL.md and CHECKLIST.md all instruct
        agents to write it, so --strict blocking a commit over it would have this repository
        contradicting its own documented convention.
        """
        for marker in ["# --- TODO: finish this ---",
                       "# === evolve: O(n^2) scan, fine under 10k rows ===",
                       "# ---- noqa: E501 ----"]:
            self.assertEqual(tiers(marker + "\nvalue = 1\n"), [], marker)

    def test_decoration_does_not_launder_commented_out_code(self) -> None:
        for hidden in ["# ---- print(user) ----", "# ==== cache = {} ===="]:
            self.assertEqual(tiers(hidden + "\nvalue = 1\n"), ["noise"], hidden)

    def test_work_markers_and_directives_are_left_alone(self) -> None:
        self.assertEqual(tiers("""
            # TODO: handle negative amounts
            # FIXME: this drops the tail
            # type: ignore
            # noqa: E501
            # evolve: O(n^2) scan, fine under 10k rows; use a hash index above
            value = 1
        """), [])


class StrictTierTests(unittest.TestCase):
    def test_candidates_alone_never_fail_strict(self) -> None:
        """--strict is for hooks, so only provable noise may block a commit."""
        found = scan_source("""
            # increment the counter
            counter = counter + 1
        """)
        self.assertTrue(found)
        self.assertNotIn("noise", [tier for _, tier, _ in found])


class TargetSelectionTests(unittest.TestCase):
    """A report whose only signal is an absence must distinguish clean from never-opened."""

    def test_a_mistyped_path_is_fatal_rather_than_a_clean_bill_of_health(self) -> None:
        with self.assertRaises(SystemExit):
            comments.python_targets(ROOT, ["no_such_file.py"], None, False)

    def test_a_directory_is_fatal(self) -> None:
        with self.assertRaises(SystemExit):
            comments.python_targets(ROOT, ["scripts"], None, False)

    def test_a_real_file_is_accepted(self) -> None:
        self.assertEqual(comments.python_targets(ROOT, ["scripts/comments.py"], None, False),
                         ["scripts/comments.py"])


class UnreadableInputTests(unittest.TestCase):
    def test_an_unbalanced_file_keeps_the_comments_read_before_the_lexer_stopped(self) -> None:
        """tokenize raises at EOF inside an open bracket; list() would discard the whole batch."""
        self.assertEqual(tiers("def broken(:\n    # print(x)\n    # cache = {}\n"), ["noise"])

    def test_a_syntax_error_does_not_raise(self) -> None:
        scan_source("def broken(:\n    pass\n")

    def test_an_empty_file_is_silent(self) -> None:
        self.assertEqual(scan_source(""), [])

    def test_a_comment_only_file_is_handled(self) -> None:
        self.assertEqual(tiers("# x = 1\n"), ["noise"])


class CommentBlockTests(unittest.TestCase):
    """Consecutive own-line comments are one comment. Every case here is a real stdlib finding.

    A 30-finding hand audit of the Python standard library found that judging `#` lines
    independently caused every false positive it produced. These four are the originals.
    """

    def test_a_sentence_continued_onto_another_line(self) -> None:
        """dataclasses.py:807, where `# module).` was matched against the code below it."""
        self.assertEqual(tiers("""
            # If typing has not been imported, then it's impossible for any
            # annotation to be a ClassVar.  So, only look for ClassVar if
            # typing has been imported by any module (not necessarily cls's
            # module).
            typing = sys.modules.get('typing')
        """), [])

    def test_an_invariant_stated_across_two_lines(self) -> None:
        """fractions.py:134. The second line restates identifiers; the block states a why."""
        self.assertEqual(tiers("""
            # Adjust in the case where significand == 10**figures, to ensure that
            # 10**(figures - 1) <= significand < 10**figures.
            if len(str(significand)) == figures + 1:
                significand //= 10
        """), [])

    def test_an_example_inside_an_explanation(self) -> None:
        """typing.py:1556. An indented example is not a disabled statement."""
        self.assertEqual(tiers("""
            # Here, `C.__args__` should be (int, str) - NOT ([int], str).
            # That means that if we had something like...
            #   D = C[[int, str], float]
            # ...we need to be careful.
            args = C.__args__
        """), [])

    def test_a_row_of_an_ascii_table(self) -> None:
        """dataclasses.py:162. A rule inside a drawn table is content, not a separator."""
        self.assertEqual(tiers("""
            # | False |       |       |
            # +-------+-------+-------+
            # | True  | add   |       |
            flags = compute()
        """), [])

    def test_a_disabled_branch_parses_only_as_a_block(self) -> None:
        """Neither line is valid alone: the `if` has no body, the `return` is outside a function.

        imaplib.py, colorsys.py and zipimport.py all carry this shape, and it is the most
        worthwhile thing the tool finds, so judging lines one at a time was a real miss.
        """
        self.assertEqual(tiers("""
            def handler(content_type):
                # if content_type is None:
                #     return None
                return content_type
        """), ["noise"])

    def test_a_wholly_commented_out_block_is_still_caught(self) -> None:
        self.assertEqual(tiers("""
            # conn = sqlite3.connect("users.db")
            # c = conn.cursor()
            # result = c.fetchone()
            value = 1
        """), ["noise"])

    def test_a_block_of_pure_rules_is_still_decoration(self) -> None:
        self.assertEqual(tiers("# =========\n# ---------\nvalue = 1\n"), ["noise"])


class BaselineTests(unittest.TestCase):
    """Adopting this in a repo that already has noise is the case that decides if it survives.

    Pointed at `requests` with no baseline, the hook blocked a clean commit because utils.py
    already carried a restating docstring nine hundred lines from the edit. A gate that fails
    for someone else's old comment gets switched off, and then it protects nothing.
    """

    BEFORE = 'def old_helper(user):\n    """Old helper."""\n    return user\n'
    AFTER_CLEAN = BEFORE + '\n\ndef fresh(rows):\n    return sorted(rows)\n'
    AFTER_NOISY = BEFORE + '\n\ndef fresh(rows):\n    # cache = {}\n    return sorted(rows)\n'

    def write(self, source: str) -> str:
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "sample.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)
        return path

    def test_pre_existing_noise_is_hidden(self) -> None:
        self.assertTrue(comments.scan(self.write(self.AFTER_CLEAN)))
        self.assertEqual(comments.new_findings(self.write(self.AFTER_CLEAN), self.BEFORE), [])

    def test_newly_introduced_noise_still_fails(self) -> None:
        fresh = comments.new_findings(self.write(self.AFTER_NOISY), self.BEFORE)
        self.assertEqual([tier for _, tier, _ in fresh], ["noise"])

    def test_no_baseline_reports_everything(self) -> None:
        self.assertTrue(comments.new_findings(self.write(self.AFTER_CLEAN), None))

    def test_a_finding_that_only_moved_is_not_new(self) -> None:
        """Inserting a function above one shifts its lines without changing it."""
        moved = "import os\n\n\n" + self.BEFORE
        self.assertEqual(comments.new_findings(self.write(moved), self.BEFORE), [])

    def test_a_second_copy_of_the_same_noise_is_new(self) -> None:
        """Matching by message must count occurrences, not membership, or duplicates hide.

        Two identical `# cache = {}` lines produce byte-identical messages, so a set would
        treat the second one as already known and wave it through.
        """
        once = "# cache = {}\nvalue = 1\n"
        twice = "# cache = {}\nvalue = 1\n\n\n# cache = {}\nother = 2\n"
        self.assertEqual(len(comments.scan(self.write(twice))), 2)
        self.assertEqual(len(comments.new_findings(self.write(twice), once)), 1)


class QuietTests(unittest.TestCase):
    def test_scanning_emits_no_warnings_of_its_own(self) -> None:
        """A regex with a bare backslash made ast.parse warn onto stderr, into the report."""
        source = 'import re\nPAT = re.compile("\\\\s+")\n# old = re.compile("\\\\d+")\nx = 1\n'
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            scan_source(source)
        self.assertEqual([str(w.message) for w in caught], [])


class RepositoryCalibrationTests(unittest.TestCase):
    """The reporter must stay silent on this repository's own why-comments.

    These files carry postmortems of real incidents (the `git checkout -- .` data loss in
    autoevolve.py, the same-module caller blind spot in callers.py). If a change to the
    detectors starts flagging them, the detectors are wrong, not the comments.
    """

    FILES = ["autoevolve.py", "scripts/callers.py", "scripts/check.py", "scripts/comments.py",
             "scripts/ruler.py", "scripts/branch.py", "scripts/run_quiet.py",
             "scripts/build_adapters.py", "scripts/check_target.py", "scripts/corpus_audit.py",
             "scripts/ruler_audit.py"]

    def test_no_noise_in_the_repositorys_own_sources(self) -> None:
        offenders = []
        for rel in self.FILES:
            for line, tier, message in comments.scan(os.path.join(ROOT, rel)):
                if tier == "noise":
                    offenders.append(f"{rel}:{line}  {message}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
