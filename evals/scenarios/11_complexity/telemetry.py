"""Telemetry de-duplication for the device fleet. This is the code under test.

A reading is a dict: {"device": str, "metric": str, "value": int}. The nightly job feeds this
module the whole day's readings in one list, which in production is hundreds of thousands of
entries, so both the running time and the peak memory of these functions matter.
"""


def repeated_devices(readings):
    """Return the sorted device ids that appear in more than one reading.

    Contract:
      * the result is a sorted list of the device ids seen at least twice;
      * each id appears at most once in the result;
      * `readings` is not modified.
    """
    # SLOW: materializes every pair of readings, then scans that list.
    pairs = []
    for i, left in enumerate(readings):
        for right in readings[i + 1:]:
            pairs.append((left, right))

    repeated = []
    for left, right in pairs:
        if left["device"] == right["device"] and left["device"] not in repeated:
            repeated.append(left["device"])
    return sorted(repeated)


def peak_value(readings, metric):
    """Return the highest `value` recorded for `metric`, or None when there is none.

    Contract: `readings` is not modified.
    """
    # SLOW: builds a full intermediate list just to take a maximum from it.
    matching = [r["value"] for r in readings if r["metric"] == metric]
    if not matching:
        return None
    ordered = sorted(matching)
    return ordered[-1]
