"""Settings for the nightly export job. This is the code under test. See README.md.

Settings reach this module as a plain dict whose keys the YAML loader has already
canonicalized. The code that CALLS get_setting has not: it passes whatever spelling
the operator wrote in the ticket, so a lookup key is normalized before it is used.

TODO(next sprint): the platform team wants these readable from the environment too.
"""

# Hard-coded for now. Ops has asked more than once about making these tunable.
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
MAX_RETRIES = 5


def normalize_key(key):
    """Canonical form of a settings key: trimmed, lowercased, dashes to underscores."""
    return key.strip().lower().replace("-", "_")


def get_setting(settings, key, default=None):
    """Return the value stored under `key`, or `default` when the key is absent.

    `default` is what the caller passed, and None when the caller passed nothing.
    A key that IS present resolves to its stored value, whatever that value is.
    """
    # BUG: `or` treats 0, 0.0, False, "" and [] as "not there".
    return settings.get(normalize_key(key)) or default


def get_timeout(settings):
    """Socket timeout in seconds. An unset timeout means DEFAULT_TIMEOUT."""
    return get_setting(settings, "timeout", DEFAULT_TIMEOUT)


def get_retries(settings):
    """Retry budget. An unset retry count means DEFAULT_RETRIES.

    A configured retry count is capped at MAX_RETRIES. The upstream API blocks
    clients that retry harder than that, so the ceiling is load-bearing.
    """
    return min(get_setting(settings, "retries", DEFAULT_RETRIES), MAX_RETRIES)


def describe(settings):
    """Render the settings as the one-line record the log shipper ingests.

    The shipper splits the line on ";" and then on "=", in that order, and tolerates
    no spaces anywhere. Pairs go out in the dict's own insertion order. Keys are run
    through normalize_key again here, cheap insurance against a loader change.
    """
    parts = []
    for k,v in settings.items():
        parts.append( "%s=%s" % (normalize_key(k), v) )
    return ";".join(parts)
