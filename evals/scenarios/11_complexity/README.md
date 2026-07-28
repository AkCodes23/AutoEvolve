# Scenario 11: time AND space, not just time

**Task:** `repeated_devices(readings)` returns the sorted device ids seen more than once, and
`peak_value(readings, metric)` returns the highest value recorded for a metric. Both are correct
today and both are wasteful. The nightly job passes hundreds of thousands of readings, so make
them efficient without changing what they return, and without modifying the caller's list.

## Why this scenario exists

`02_optimize` measures a single quadratic loop. Nothing else in the suite measured **memory** at
all, so a solution could halve the running time while still materialising a list it never needed
and score full marks. That is a real and common shape of "optimised" code.

Here the two axes come apart on purpose:

- `repeated_devices` builds every pair of readings: quadratic in **time and space**.
- `peak_value` is already linear in time, but allocates a whole intermediate list plus a sorted
  copy just to take a maximum. Its time complexity is fine; its space complexity is not.

A fix that only kills the obvious quadratic scores 6 of 7. Both axes have to be seen.

## The signal

Seven checks:

1. `repeated_devices` correctness, including the empty list, a single reading, and an id that
   appears three times (it must still be listed once).
2. `peak_value` correctness, including an absent metric and an empty list (both `None`).
3. Neither function modifies the readings it was given. Sorting the caller's list in place is a
   classic optimisation shortcut and a contract break.
4. **Time**: counted equality and hash operations on probe device ids, budgeted per reading.
   Never wall-clock, which is machine-dependent and cannot separate the cases reliably.
5. **Space**: peak allocation for `repeated_devices`, budgeted per reading. It is allowed to be
   linear, since it must remember which ids it has seen.
6. **Space**: peak allocation for `peak_value`, capped at a constant regardless of input size,
   because a single pass needs no container at all. A streaming solution measures 0 bytes.
7. Both functions still agree with a reference implementation on a large input.

Correctness gates the efficiency checks: a fast wrong answer always scores below a slow right one.

```bash
python3 evals/run.py 11_complexity
```

## What a good run looks like

The starter scores 4/7. A solution that fixes only `repeated_devices` scores 6/7 and the detail
string says exactly which axis it left alone. A solution that fixes both scores 7/7:

- `repeated_devices`: one pass, a `set` of ids seen and a `set` of ids seen twice.
- `peak_value`: one pass keeping a running maximum, no intermediate list, no sort.
