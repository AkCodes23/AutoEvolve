"""User authentication module. This is the code under test. See grade.py.

VULNERABILITIES:
- get_user_file() is vulnerable to path traversal
- authenticate() compares passwords in plaintext (no hashing)
- build_query() is vulnerable to SQL injection
- get_config() reads arbitrary files without path restriction

Fix all security issues while preserving correct behavior for valid inputs.
"""
import os

USERS_DIR = os.path.join(os.path.dirname(__file__), "users")
ALLOWED_CONFIG = os.path.join(os.path.dirname(__file__), "config.ini")


def get_user_file(username):
    """Return the path to a user's profile file."""
    # BUG: path traversal - username like "../../etc/passwd" escapes USERS_DIR
    return os.path.join(USERS_DIR, username + ".txt")


def authenticate(username, password):
    """Check credentials. Returns True if valid, False otherwise."""
    stored = _lookup_password(username)
    if stored is None:
        return False
    # BUG: plaintext comparison - should use constant-time comparison
    # to avoid timing attacks, and passwords should be hashed
    return password == stored


def build_query(table, username):
    """Build a SQL query string to look up a user."""
    # BUG: SQL injection - username is interpolated directly
    return f"SELECT * FROM {table} WHERE username = '{username}'"


def get_config(filepath):
    """Read a configuration file and return its contents."""
    # BUG: no restriction on which files can be read
    with open(filepath, "r") as f:
        return f.read()


def _lookup_password(username):
    """Stub: in production this would query a database."""
    db = {"alice": "password123", "bob": "hunter2"}
    return db.get(username)
