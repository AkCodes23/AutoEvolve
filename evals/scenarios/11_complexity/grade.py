"""Grader for 11_complexity. Kept separate from telemetry.py (the code under test).

This is the only scenario that grades TIME and SPACE together, because a fix can easily improve
one and leave the other alone. `repeated_devices` is quadratic in both; `peak_value` is linear in
time but allocates a whole intermediate list it does not need, so a solution that only fixes the
obvious quadratic still loses the space checks.

How each axis is measured, and why not the obvious way:

  TIME is a counted number of equality and hash operations on probe elements, never wall-clock.
  Timing is machine-dependent: measured over 100 trials on this suite's sibling scenario it
  false-failed correct code and false-passed quadratic code often enough that no threshold
  separated them. A grader whose verdict moves with machine load is not a frozen signal, so the
  clock appears here only in advisory detail strings.

  SPACE is peak allocation measured with tracemalloc. Inputs are built BEFORE the peak counter
  is reset, so the reading is the memory the function itself allocates rather than the memory of
  its argument. The GATE is an absolute budget, and the doubling ratio is advisory only. The
  ratio was tried as a gate and rejected: hash containers grow capacity in power-of-two steps, so
  a correct set-based solution measured a ratio of 4.0 purely because one input size sat just
  above a resize threshold. That is the wall-clock mistake wearing a different hat, and it
  false-failed the reference solution before it was caught.

Correctness gates both. A fast wrong answer scores below a slow right one, always.
"""
import importlib
import os
import sys
import time
import tracemalloc

HERE = os.path.dirname(os.path.abspath(__file__))

# A hash-based pass costs a small constant per reading. A pairwise scan costs about n/2 per
# reading. Measured: dict/set solutions land near 2 per element, the quadratic starter near 200.
OPS_PER_ELEMENT_BUDGET = 12
# Bytes of NEW allocation per input element for repeated_devices, which must keep a set of
# device ids and so is allowed to be linear. Measured: set-based solutions land at 32 to 62 bytes
# per element, the quadratic starter at about 43,000.
BYTES_PER_ELEMENT_BUDGET = 400
# peak_value needs NO container at all: a single pass keeps one running maximum. Measured: a
# streaming solution allocates 0 bytes at every input size, while building an intermediate list
# allocates about 10,000 at n=1200 and grows from there. This is an absolute cap, not a
# per-element one, because the correct answer is constant space.
PEAK_VALUE_BYTES_CAP = 2048
# NOT a gate. Peak allocation doubling was tried as one and rejected: hash containers grow their
# capacity in power-of-two steps, so a correct set-based solution can show a ratio of 4.0 purely
# because one input size sits just above a resize threshold and the other just below. That is the
# same mistake as gating on wall-clock, in a different costume. Reported for a human to read.
SPACE_RATIO_ADVISORY = 2.5

CHECK_NAMES = (
    "repeated_devices: correct, sorted, de-duplicated device ids",
    "peak_value: correct maximum, and None when the metric is absent",
    "neither function modifies the readings it was given",
    f"repeated_devices runs in sub-quadratic time (at most {OPS_PER_ELEMENT_BUDGET} comparisons per reading)",
    f"repeated_devices uses sub-quadratic space (under {BYTES_PER_ELEMENT_BUDGET} bytes per reading)",
    f"peak_value uses constant extra space (under {PEAK_VALUE_BYTES_CAP} bytes at any input size)",
    "both stay correct on a large input",
)


class _Probe(str):
    """A device id that counts every comparison and hash performed against it.

    Subclassing str keeps it usable anywhere a device id is (sorting, dict keys, formatting),
    while making the work visible. The counter is a class attribute so every instance shares it.
    """

    __slots__ = ()
    ops = [0]

    def __eq__(self, other):
        _Probe.ops[0] += 1
        return str.__eq__(self, other)

    def __ne__(self, other):
        _Probe.ops[0] += 1
        return str.__ne__(self, other)

    def __hash__(self):
        _Probe.ops[0] += 1
        return str.__hash__(self)


def _readings(n, distinct=None):
    """n readings over `distinct` device ids, alternating between two metrics."""
    distinct = distinct or max(n // 2, 1)
    return [
        {"device": f"dev-{i % distinct}", "metric": "cpu" if i % 2 else "mem", "value": i % 977}
        for i in range(n)
    ]


def _probe_readings(n):
    distinct = max(n // 2, 1)
    return [
        {"device": _Probe(f"dev-{i % distinct}"), "metric": "cpu" if i % 2 else "mem",
         "value": i % 977}
        for i in range(n)
    ]


def _peak_bytes(fn, *args):
    """Peak bytes allocated by fn(*args). Arguments are built by the caller beforehand, so the
    input's own memory is not charged to the function under test."""
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        fn(*args)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def _elapsed(fn, *args):
    start = time.perf_counter()
    fn(*args)
    return time.perf_counter() - start


def _expected_repeated(readings):
    seen, twice = set(), set()
    for r in readings:
        key = str(r["device"])
        if key in seen:
            twice.add(key)
        seen.add(key)
    return sorted(twice)


def _checks():
    try:
        import telemetry
        importlib.reload(telemetry)
        repeated_devices = telemetry.repeated_devices
        peak_value = telemetry.peak_value
        if not callable(repeated_devices) or not callable(peak_value):
            raise TypeError("repeated_devices and peak_value must both be callable")
    except Exception as exc:  # noqa: BLE001 - an unusable submission fails, it is not a bug
        reason = f"telemetry.py did not provide both functions: {type(exc).__name__}: {exc}"
        return [(name, False, reason) for name in CHECK_NAMES]

    results = []

    def record(index, fn):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001 - a failing candidate is a failed check
            ok, detail = False, f"raised {type(exc).__name__}: {exc}"
        results.append((CHECK_NAMES[index], bool(ok), detail))

    def correct_repeated():
        cases = [
            ([], []),
            ([{"device": "a", "metric": "cpu", "value": 1}], []),
            ([{"device": "a", "metric": "cpu", "value": 1},
              {"device": "a", "metric": "mem", "value": 2}], ["a"]),
            ([{"device": "b", "metric": "cpu", "value": 1},
              {"device": "a", "metric": "cpu", "value": 2},
              {"device": "b", "metric": "cpu", "value": 3},
              {"device": "a", "metric": "cpu", "value": 4},
              {"device": "c", "metric": "cpu", "value": 5}], ["a", "b"]),
            # three occurrences must still yield the id exactly once
            ([{"device": "z", "metric": "cpu", "value": i} for i in range(3)], ["z"]),
        ]
        for readings, expected in cases:
            got = repeated_devices(list(readings))
            if list(got) != expected:
                return False, f"repeated_devices({len(readings)} readings) returned {got!r}, expected {expected!r}"
        return True, ""

    def correct_peak():
        readings = [
            {"device": "a", "metric": "cpu", "value": 5},
            {"device": "b", "metric": "mem", "value": 90},
            {"device": "c", "metric": "cpu", "value": 42},
        ]
        if peak_value(readings, "cpu") != 42:
            return False, f"peak_value(..., 'cpu') returned {peak_value(readings, 'cpu')!r}, expected 42"
        if peak_value(readings, "mem") != 90:
            return False, "peak_value(..., 'mem') did not return 90"
        if peak_value(readings, "disk") is not None:
            return False, "peak_value for an absent metric must return None"
        if peak_value([], "cpu") is not None:
            return False, "peak_value([], 'cpu') must return None"
        return True, ""

    def no_mutation():
        readings = _readings(40)
        snapshot = [dict(r) for r in readings]
        repeated_devices(readings)
        peak_value(readings, "cpu")
        if readings != snapshot:
            return False, "the readings list or its dicts were modified in place"
        return True, ""

    def time_complexity():
        n = 800
        _Probe.ops[0] = 0
        data = _probe_readings(n)
        baseline = _Probe.ops[0]  # probes cost a few ops just to be built
        _Probe.ops[0] = 0
        repeated_devices(data)
        used = _Probe.ops[0]
        budget = OPS_PER_ELEMENT_BUDGET * n
        advisory = _elapsed(repeated_devices, _readings(n))
        detail = (f"comparisons={used} (budget {budget}, build cost {baseline}); "
                  f"advisory wall clock {advisory * 1000:.1f}ms")
        return used <= budget, detail

    def space_repeated():
        small, large = _readings(600), _readings(1200)
        peak_small = _peak_bytes(repeated_devices, small)
        peak_large = _peak_bytes(repeated_devices, large)
        ratio = (peak_large / peak_small) if peak_small else float("inf")
        budget = BYTES_PER_ELEMENT_BUDGET * len(large)
        detail = (f"peak={peak_large} bytes for {len(large)} readings (budget {budget}); "
                  f"advisory doubling ratio={ratio:.1f} (a set resize alone can reach "
                  f"{SPACE_RATIO_ADVISORY}, so this is not gated)")
        return peak_large <= budget, detail

    def space_peak_value():
        large = _readings(1200)
        peak_large = _peak_bytes(peak_value, large, "cpu")
        detail = (f"peak={peak_large} bytes for {len(large)} readings "
                  f"(cap {PEAK_VALUE_BYTES_CAP}); a single pass over the readings needs no "
                  f"intermediate container and measures 0")
        return peak_large <= PEAK_VALUE_BYTES_CAP, detail

    def large_input_still_correct():
        readings = _readings(5000)
        expected = _expected_repeated(readings)
        got = repeated_devices(readings)
        if list(got) != expected:
            return False, f"repeated_devices disagreed with the reference on {len(readings)} readings"
        values = [r["value"] for r in readings if r["metric"] == "cpu"]
        if peak_value(readings, "cpu") != max(values):
            return False, "peak_value disagreed with the reference on a large input"
        return True, ""

    for index, probe in enumerate((correct_repeated, correct_peak, no_mutation, time_complexity,
                                   space_repeated, space_peak_value, large_input_still_correct)):
        record(index, probe)
    return results


def checks():
    """Run the graded checks with this scenario's directory on sys.path, then clean up."""
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
