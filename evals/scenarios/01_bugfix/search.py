"""A tiny first-letter search index. This is the code under test. See README.md.

BUG: search() crashes on an empty query, and every caller inherits the crash.
Fix it at the root so all three callers are covered by one change.
"""

_INDEX: dict[str, list[str]] = {}
for _word in ["apple", "apricot", "banana", "cherry"]:
    _INDEX.setdefault(_word[0], []).append(_word)


def search(query):
    # BUG: query[0] raises on an empty query. Guard it here (the root), not per caller.
    return _INDEX[query[0]]


# Three call sites, all routed through search():

def suggest(prefix):
    return search(prefix)


def count_matches(prefix):
    return len(search(prefix))


def has_match(prefix):
    return len(search(prefix)) > 0
