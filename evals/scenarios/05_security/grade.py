"""Grader for 05_security. Kept separate from user_auth.py (the code under test).

The signal: the agent must fix path traversal, SQL injection, plaintext password
comparison, and unrestricted file reading — while preserving correct behavior for
valid inputs.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import user_auth
    importlib.reload(user_auth)

    def run(fn):
        try:
            return bool(fn()), ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    cases = [
        # Path traversal must be blocked
        (
            'get_user_file("../../etc/passwd") is contained within USERS_DIR',
            lambda: _path_is_safe(user_auth),
        ),
        # SQL injection must be parameterized or escaped
        (
            "build_query resists SQL injection via single-quote",
            lambda: _no_sql_injection(user_auth),
        ),
        # Plaintext password comparison must use constant-time or hashing
        (
            "authenticate uses hmac.compare_digest or hashing",
            lambda: _uses_safe_comparison(user_auth),
        ),
        # Unrestricted file read must be bounded
        (
            "get_config rejects paths outside allowed directory",
            lambda: _config_restricted(user_auth),
        ),
        # Valid behavior must still work
        (
            'authenticate("alice", "password123") still returns True',
            lambda: _valid_auth_works(user_auth),
        ),
    ]
    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out


def _path_is_safe(mod):
    """Path traversal: the resolved path must stay inside USERS_DIR."""
    try:
        result = mod.get_user_file("../../etc/passwd")
        resolved = os.path.realpath(result)
        users_dir = os.path.realpath(mod.USERS_DIR)
        # Either it raises, or the path is inside USERS_DIR
        return resolved.startswith(users_dir)
    except (ValueError, OSError, PermissionError):
        # Raising on traversal attempt is also acceptable
        return True


def _no_sql_injection(mod):
    """SQL injection: a single-quote in username must not break the query structure."""
    malicious = "admin'; DROP TABLE users;--"
    query = mod.build_query("users", malicious)
    # The raw injection would produce: WHERE username = 'admin'; DROP TABLE users;--'
    # A safe version either parameterizes (returns a tuple/placeholder) or escapes the quote
    if isinstance(query, tuple):
        # Parameterized: (query_string, params)
        return True
    if isinstance(query, str):
        # Must not have unescaped single quote from user input
        # The malicious string has "'" — if it appears raw in the SQL, it's broken
        return "'; DROP TABLE" not in query
    return False


def _uses_safe_comparison(mod):
    """Check that the module uses hmac.compare_digest or a hashing library."""
    import inspect
    source = inspect.getsource(mod.authenticate)
    # Accept: hmac.compare_digest, hashlib, bcrypt, passlib, werkzeug.security
    safe_markers = [
        "compare_digest", "hashlib", "bcrypt", "passlib",
        "check_password", "verify", "pbkdf2", "scrypt", "argon2",
    ]
    return any(marker in source for marker in safe_markers)


def _config_restricted(mod):
    """get_config must reject paths outside the allowed config location."""
    try:
        # Try reading a file that is NOT the allowed config
        mod.get_config("/etc/passwd")
        # If it doesn't raise, it's unrestricted
        return False
    except (ValueError, PermissionError, OSError):
        return True


def _valid_auth_works(mod):
    """Valid credentials must still authenticate successfully."""
    # The agent might hash stored passwords, so we check the module's
    # authenticate function works for known-good credentials.
    # Since the stub _lookup_password has plaintext, the agent needs to
    # either keep the stub working or hash both sides consistently.
    return mod.authenticate("alice", "password123") is True
