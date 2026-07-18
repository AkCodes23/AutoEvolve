"""Order-preserving de-duplication. Code under test. See README.md.

BUG: this is O(n^2). It scans the growing result list for every item. Make it faster
without changing behavior: the output and its order must stay identical.
"""


def dedupe(items):
    out = []
    for x in items:
        if x not in out:  # O(n) membership scan inside an O(n) loop, so O(n^2) overall
            out.append(x)
    return out
