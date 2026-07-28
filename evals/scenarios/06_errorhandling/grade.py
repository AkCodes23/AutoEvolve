"""Grader for 06_errorhandling. Kept separate from pipeline.py (the code under test).

The signal: the agent must add proper input validation, handle edge cases, categorize
errors properly (not swallow them), and preserve correct behavior for valid inputs.

Grading rules this file follows on purpose:
- Every documented failure mode is paired with a SUCCESS case, so "make every function
  return None" cannot score full marks.
- Nothing is graded by reading source text. Only behavior is exercised.
- Where several implementations are equally reasonable (raise vs return a falsy value,
  ValueError vs KeyError for a missing key), every reasonable option is accepted, so a
  minimal idiomatic fix is never punished for style.

KNOWN LIMIT, so nobody over-reads the score. Two of these checks are NON-DISCRIMINATING: the
untouched starter already passes "process_records rejects non-list input" and "calculate_average
rejects non-numeric values", because `len(None)` and `sum(["a", "b"])` raise TypeError all by
themselves. They are kept because a solution that removed that behaviour would be worse, but
they are regression guards, not evidence of deliberate validation, and no input can make them
discriminate: any non-list or non-numeric value that reaches unguarded code raises the same
exception type a deliberate guard would. Read this scenario as roughly 11 discriminating checks
out of 13.
"""
import importlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _cases():
    """(check name, probe) pairs. Each probe takes the module under test.

    Kept at module level so an unimportable submission can still be reported as this exact
    set of failed checks. If the import escaped checks(), run.py would print "[ERROR] the
    grader itself failed to run (this is a harness bug)" and evals/profile.py would record
    outcome=grader_error with checks_total=None, which DROPS the trial from the published
    averages instead of scoring it zero.
    """
    return (
        # --- process_records: failure modes then success ---
        (
            "process_records rejects non-list input (None, 42) with TypeError or ValueError",
            _records_reject_non_list,
        ),
        (
            "process_records([]) returns an empty summary or raises ValueError "
            "(not ZeroDivisionError)",
            _records_empty_is_handled,
        ),
        (
            "process_records tolerates a record missing 'value' (raises, or ignores it)",
            _records_missing_key,
        ),
        (
            "process_records returns correct total/count/average for valid records",
            _records_happy_path,
        ),
        # --- calculate_average: failure modes then success ---
        (
            "calculate_average([]) raises ValueError (not ZeroDivisionError)",
            _avg_empty_raises_valueerror,
        ),
        (
            "calculate_average rejects non-numeric values with TypeError or ValueError",
            _avg_rejects_non_numeric,
        ),
        (
            "calculate_average returns the exact mean for several inputs",
            _avg_happy_path,
        ),
        # --- parse_date: failure modes then success ---
        (
            "parse_date rejects malformed date strings with ValueError",
            _parse_rejects_garbage,
        ),
        (
            "parse_date(None) raises TypeError or ValueError (not AttributeError)",
            _parse_rejects_none,
        ),
        (
            "parse_date returns the correct fields for several valid dates",
            _parse_happy_path,
        ),
        # --- write_output: success then failure modes ---
        (
            "write_output actually writes the data to a writable path",
            _write_happy_path,
        ),
        (
            "write_output reports failure for an unwritable destination "
            "(falsy return or raised OSError)",
            _write_reports_failure,
        ),
        (
            "write_output does not claim success for data it cannot write",
            _write_rejects_bad_data,
        ),
    )


def _checks():
    cases = _cases()
    try:
        import pipeline
        importlib.reload(pipeline)
    except Exception as e:  # noqa: BLE001 - an unusable submission fails, it is not a bug
        reason = f"pipeline.py did not import: {type(e).__name__}: {e}"[:160]
        return [(name, False, reason) for name, _ in cases]

    def run(fn):
        try:
            outcome = fn(pipeline)
        except Exception as e:
            return False, f"grader hit {type(e).__name__}: {e}"
        if isinstance(outcome, tuple):
            ok, detail = outcome
            return bool(ok), detail
        return bool(outcome), ""

    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out


# --------------------------------------------------------------------------------------
# helpers. Each returns True/False, or (ok, detail) when a detail helps the reader.
# --------------------------------------------------------------------------------------


def _raises(fn, allowed):
    """Return (ok, detail) for 'fn() raised one of `allowed`'.

    A wrong exception type and a silent return are both failures, so "return None"
    can never be mistaken for validation.
    """
    try:
        result = fn()
    except allowed:
        return True, ""
    except BaseException as e:  # noqa: BLE001 - any other type is the wrong answer
        names = "/".join(t.__name__ for t in allowed)
        return False, f"raised {type(e).__name__}, expected {names}"
    names = "/".join(t.__name__ for t in allowed)
    return False, f"returned {result!r} instead of raising {names}"


def _records_reject_non_list(mod):
    # Both inputs are non-iterable, so every reasonable implementation (explicit
    # isinstance guard or plain iteration) lands on TypeError or ValueError.
    for bad in (None, 42):
        ok, detail = _raises(lambda: mod.process_records(bad), (TypeError, ValueError))
        if not ok:
            return False, f"process_records({bad!r}): {detail}"
    return True, ""


def _records_empty_is_handled(mod):
    """An empty batch is not an internal error: summarize it or reject it explicitly."""
    try:
        result = mod.process_records([])
    except ValueError:
        return True, ""
    except Exception as e:
        return False, f"raised {type(e).__name__}, expected a summary or ValueError"
    if not isinstance(result, dict):
        return False, f"returned {result!r}, expected a summary dict or ValueError"
    if result.get("count") != 0 or result.get("total") not in (0, 0.0):
        return False, f"returned {result!r}, expected total 0 and count 0"
    if "average" in result and result["average"] not in (0, 0.0, None):
        return False, f"average for an empty batch was {result['average']!r}"
    return True, ""


def _records_missing_key(mod):
    """Raising or ignoring the bad record are both fine. Miscounting it is not."""
    records = [{"value": 10}, {"no_value_here": 1}]
    try:
        result = mod.process_records(records)
    except (KeyError, TypeError, ValueError):
        return True, ""
    except Exception as e:
        return False, f"raised {type(e).__name__}, expected KeyError/TypeError/ValueError"
    if isinstance(result, dict) and result.get("total") in (10, 10.0):
        return True, ""
    return False, f"returned {result!r}, expected a raise or a summary with total 10"


def _records_happy_path(mod):
    """Two datasets, so a hardcoded answer cannot pass."""
    datasets = [
        ([{"value": 10}, {"value": 20}], 30, 2, 15.0),
        ([{"value": 3}, {"value": 4}, {"value": 5}], 12, 3, 4.0),
    ]
    for records, total, count, average in datasets:
        result = mod.process_records(records)
        if not isinstance(result, dict):
            return False, f"process_records({records!r}) returned {result!r}"
        got = (result.get("total"), result.get("count"), result.get("average"))
        if got != (total, count, average):
            return False, f"process_records({records!r}) gave {got}, expected {(total, count, average)}"
    return True, ""


def _avg_empty_raises_valueerror(mod):
    # ZeroDivisionError leaking out is the bug being graded, so only ValueError counts.
    return _raises(lambda: mod.calculate_average([]), (ValueError,))


def _avg_rejects_non_numeric(mod):
    for bad in (["a", "b"], [1, None]):
        ok, detail = _raises(lambda: mod.calculate_average(bad), (TypeError, ValueError))
        if not ok:
            return False, f"calculate_average({bad!r}): {detail}"
    return True, ""


def _avg_happy_path(mod):
    for numbers, expected in (([1, 2, 3], 2.0), ([2.5, 3.5], 3.0), ([10], 10.0), ([-1, 1], 0.0)):
        got = mod.calculate_average(numbers)
        if got != expected:
            return False, f"calculate_average({numbers!r}) returned {got!r}, expected {expected}"
    return True, ""


def _parse_rejects_garbage(mod):
    # All of these are malformed under any reading of "YYYY-MM-DD", so no
    # implementation choice (strptime, regex, manual split) is penalized here.
    for bad in ("not-a-date", "", "2024/03/15", "2024-03", "abc-de-fgh"):
        ok, detail = _raises(lambda: mod.parse_date(bad), (ValueError,))
        if not ok:
            return False, f"parse_date({bad!r}): {detail}"
    return True, ""


def _parse_rejects_none(mod):
    return _raises(lambda: mod.parse_date(None), (TypeError, ValueError))


def _parse_happy_path(mod):
    """Several dates, so a hardcoded dict cannot pass. Extra keys are allowed."""
    for text, year, month, day in (
        ("2024-03-15", 2024, 3, 15),
        ("1999-12-31", 1999, 12, 31),
        ("2000-01-01", 2000, 1, 1),
    ):
        result = mod.parse_date(text)
        if not isinstance(result, dict):
            return False, f"parse_date({text!r}) returned {result!r}"
        got = (result.get("year"), result.get("month"), result.get("day"))
        if got != (year, month, day):
            return False, f"parse_date({text!r}) gave {got}, expected {(year, month, day)}"
    return True, ""


def _write_and_read(mod, data):
    """Call write_output on a fresh writable path. Return (return_value, file_text)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.txt")
        returned = mod.write_output(data, path)
        if not os.path.exists(path):
            return returned, None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return returned, f.read()


def _write_happy_path(mod):
    """The file must really contain the data. Format is the author's choice, so this
    only requires every key and value to appear somewhere in the text. The return
    value is deliberately not constrained here: returning None on success and raising
    on failure is as valid as returning True/False.
    """
    data = {"alpha": "one", "beta": "two"}
    returned, text = _write_and_read(mod, data)
    if text is None:
        return False, f"no file was created (returned {returned!r})"
    missing = [s for s in ("alpha", "one", "beta", "two") if s not in text]
    if missing:
        return False, f"file is missing {missing}, contents were {text!r}"
    if returned is False:
        return False, "wrote the file but reported failure by returning False"
    return True, ""


def _unwritable_path(tmp):
    """A destination that cannot be written even if the code creates parent dirs:
    a regular file is used as a directory component."""
    blocker = os.path.join(tmp, "blocker")
    with open(blocker, "w", encoding="utf-8") as f:
        f.write("not a directory\n")
    return os.path.join(blocker, "out.txt")


def _write_reports_failure(mod):
    """Failure must reach the caller. Two answers are equally correct: return a falsy
    value (False or None), or let the OSError propagate. Returning a truthy value is
    the bug. A module that returns the same falsy value on success and on failure is
    also wrong, because the caller still cannot tell the two apart.
    """
    data = {"key": "value"}
    success_return, _ = _write_and_read(mod, data)
    with tempfile.TemporaryDirectory() as tmp:
        target = _unwritable_path(tmp)
        try:
            returned = mod.write_output(data, target)
        except OSError:
            return True, ""
        except Exception as e:
            return False, f"raised {type(e).__name__}, expected OSError or a falsy return"
    if returned:
        return False, f"returned {returned!r} for an unwritable destination"
    if not success_return:
        return False, (
            f"returned {returned!r} on failure and {success_return!r} on success, "
            "so the caller cannot tell them apart"
        )
    return True, ""


def _write_rejects_bad_data(mod):
    """Silently swallowing every error is the bug. Data the writer cannot handle must
    not come back as success. Raising or returning a falsy value are both accepted.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.txt")
        try:
            returned = mod.write_output(["not", "a", "mapping"], path)
        except Exception:
            return True, ""
    if returned:
        return False, f"returned {returned!r} for data it cannot write"
    return True, ""


def checks():
    """Run the graded checks with this scenario's directory on sys.path, then clean up.

    Both the path entry and the imported module are removed afterwards. `run.py --all` grades
    every scenario in ONE interpreter, so a leaked path entry plus a cached module means the
    first scenario to claim a module name wins: a later scenario whose code file shares that
    name would be graded against the wrong file, silently and with a plausible-looking score.
    No two scenarios share a filename today, which is exactly why this is worth fixing now
    rather than after it produces a wrong number.
    """
    added = HERE not in sys.path
    if added:
        sys.path.insert(0, HERE)
    try:
        return _checks()
    finally:
        if added and HERE in sys.path:
            sys.path.remove(HERE)
        for name, module in list(sys.modules.items()):
            origin = getattr(module, "__file__", None) or ""
            if origin and os.path.dirname(os.path.abspath(origin)) == HERE:
                del sys.modules[name]
