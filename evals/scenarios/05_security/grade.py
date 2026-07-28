"""Grader for 05_security. Kept separate from user_auth.py (the code under test).

The signal: the agent must fix path traversal, SQL injection, plaintext password storage,
and unrestricted file reading, while preserving correct behavior for valid inputs.

Every check exercises BEHAVIOR. Nothing here reads the solution's source text, so any
implementation that really holds the property passes whatever its style, and a comment
that merely mentions "hashlib" proves nothing. The contracts, stated once so a solution
can aim at them:

- get_user_file(name): for a name that escapes USERS_DIR, either raise or return a path
  contained in USERS_DIR (containment by os.path.commonpath, so a sibling directory whose
  name merely starts with USERS_DIR does not count). For a valid user, yield that user's
  profile file: its path or its contents, either is accepted.
- build_query(table, username): return something sqlite3 can execute, a SQL string or a
  (sql, params) pair. Executed against a real table it must select ZERO rows for an
  injection payload and the matching row for a valid username. Both textbook remediations
  pass: binding parameters, or doubling the quotes. A raw payload inside the SQL text of a
  (sql, params) pair is rejected even before execution.
- authenticate(user, password): accept the right password, reject wrong ones, and do not
  keep the password in plaintext. The stored credential must differ from the password and
  must not itself be accepted as one.
- get_config(path): never return the contents of a file outside the allowed config
  location, and still return the allowed config for the valid call. The probe uses a real
  canary file, so a FileNotFoundError from the absolute probe is inconclusive and counts
  as a failure, never as a pass. The canary is itself named config.ini, so a solution that
  reduces the argument to a basename inside the allowed directory still passes.

Fixtures (users/alice.txt and config.ini) ship next to this file. When the tree is not
writable, the profiler grades inside a read only mount, they are planted in a temp tree
and the module's path constants are repointed at it.
"""
import importlib
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

PLAINTEXT = "password123"
ALICE_MARKER = "demo-profile-fixture-05-security"
CONFIG_MARKER = "config-fixture-05-security"
CANARY_MARKER = "canary-outside-the-allowed-directory-05-security"

ALICE_TEXT = f"alice\n{ALICE_MARKER}\nEval scaffolding only. Not a real account, no secrets here.\n"
CONFIG_TEXT = f"[demo]\nname = {CONFIG_MARKER}\nretries = 3\n; Eval scaffolding only.\n"
CANARY_TEXT = f"{CANARY_MARKER}\nIf a check sees this text, the module read a file it should have refused.\n"


def _checks():
    cases = [
        ("get_user_file refuses names that escape USERS_DIR", _check_traversal),
        ('get_user_file("alice") still yields the alice profile', _check_user_happy_path),
        ("build_query selects zero rows for SQL injection payloads", _check_sql_injection),
        ("build_query still selects the row for a valid username", _check_sql_valid),
        ("authenticate does not keep the password in plaintext", _check_password_storage),
        ("authenticate accepts the right password and rejects wrong ones", _check_auth_behavior),
        ("get_config refuses a file outside the allowed directory", _check_config_refusal),
        ("get_config still returns the allowed config contents", _check_config_happy_path),
    ]
    try:
        import user_auth
        mod = importlib.reload(user_auth)
    except Exception as exc:  # noqa: BLE001 - an unimportable module fails every check
        detail = f"user_auth did not import: {type(exc).__name__}: {exc}"
        return [(name, False, _clip(detail)) for name, _ in cases]

    cleanups = []
    out = []
    try:
        env = _setup(mod, cleanups)
        for name, fn in cases:
            try:
                ok, detail = fn(mod, env)
            except Exception as exc:  # noqa: BLE001 - a probe must never abort the grader
                ok, detail = False, f"probe raised {type(exc).__name__}: {exc}"
            out.append((name, bool(ok), _clip(detail)))
    finally:
        for fn in reversed(cleanups):
            try:
                fn()
            except OSError:
                pass
    return out


# --------------------------------------------------------------------------- setup


def _setup(mod, cleanups):
    """Plant the fixtures the happy paths need and the canaries the refusals need."""
    canary_dir = tempfile.mkdtemp(prefix="autoevolve_canary_")
    cleanups.append(lambda: shutil.rmtree(canary_dir, ignore_errors=True))
    # The config canary is named config.ini on purpose: reducing the argument to its
    # basename inside the allowed directory is a real fix and must not be punished.
    for name in ("config.ini", "canary", "canary.txt"):
        _write(os.path.join(canary_dir, name), CANARY_TEXT)

    users_dir, config_path, note = _plant_fixtures(mod, cleanups)

    # A sibling directory whose name starts with USERS_DIR: the classic escape that a
    # str.startswith containment test waves through. Give it real content so a module that
    # returns file contents cannot be excused by a FileNotFoundError.
    evil_dir = users_dir + "_evil"
    if not os.path.isdir(evil_dir):
        cleanups.append(lambda: shutil.rmtree(evil_dir, ignore_errors=True))
    for name in ("secret", "secret.txt"):
        target = os.path.join(evil_dir, name)
        if not os.path.isfile(target) and _write(target, CANARY_TEXT):
            cleanups.append(lambda p=target: os.path.isfile(p) and os.remove(p))

    return {
        "users_dir": users_dir,
        "config_path": config_path,
        "canary_dir": canary_dir,
        "canary_config": os.path.join(canary_dir, "config.ini"),
        "canary_file": os.path.join(canary_dir, "canary"),
        "note": note,
    }


def _plant_fixtures(mod, cleanups):
    users_dir = os.path.normpath(str(getattr(mod, "USERS_DIR", os.path.join(HERE, "users"))))
    config_path = os.path.normpath(str(getattr(mod, "ALLOWED_CONFIG", os.path.join(HERE, "config.ini"))))
    if os.path.isdir(config_path):
        config_path = os.path.join(config_path, "config.ini")
    if _write(os.path.join(users_dir, "alice.txt"), ALICE_TEXT) and _write(config_path, CONFIG_TEXT):
        return users_dir, config_path, ""

    root = tempfile.mkdtemp(prefix="autoevolve_fixture_")
    cleanups.append(lambda: shutil.rmtree(root, ignore_errors=True))
    users_dir = os.path.join(root, "users")
    config_path = os.path.join(root, "config.ini")
    _write(os.path.join(users_dir, "alice.txt"), ALICE_TEXT)
    _write(config_path, CONFIG_TEXT)
    repointed = 0
    for attr, value in (("USERS_DIR", users_dir), ("ALLOWED_CONFIG", config_path)):
        if hasattr(mod, attr):
            setattr(mod, attr, value)
            repointed += 1
    note = "" if repointed == 2 else (
        " (fixtures unavailable: the tree is not writable and the module keeps no path "
        "constant to repoint, so this happy path could not be set up)"
    )
    return users_dir, config_path, note


def _write(path, text):
    """Create `path` with `text` unless it already exists. True when the file is there."""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if not os.path.isfile(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        return os.path.isfile(path)
    except OSError:
        return False


# ------------------------------------------------------------------------- helpers


def _clip(detail, limit=300):
    detail = " ".join(str(detail).split())
    return detail if len(detail) <= limit else detail[: limit - 3] + "..."


def _looks_like_path(value):
    if isinstance(value, os.PathLike):
        return True
    return isinstance(value, str) and "\n" not in value and "\x00" not in value and value != ""


def _contained(path, root):
    """True when `path` is inside `root`. commonpath, so users_evil/ does not sneak past."""
    try:
        p = os.path.normcase(os.path.realpath(str(path)))
        r = os.path.normcase(os.path.realpath(str(root)))
        return os.path.commonpath([p, r]) == r
    except (ValueError, OSError):
        return False


def _file_text(value):
    """The contents of `value` when it names an existing file, else None."""
    if not _looks_like_path(value):
        return None
    try:
        if not os.path.isfile(str(value)):
            return None
        with open(str(value), "r", encoding="utf-8", errors="replace") as f:
            return f.read(8192)
    except OSError:
        return None


def _as_text(value):
    """Whatever a function handed back, as text we can search for a marker."""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value if isinstance(value, str) else str(value)


def _payload_text(value):
    """Both readings of a return value: its own text, plus the file it may point at."""
    return _as_text(value) + "\n" + (_file_text(value) or "")


def _relpath(target, start):
    try:
        return os.path.relpath(target, start)
    except (ValueError, OSError):
        return None  # different Windows drives have no relative path


# --------------------------------------------------------------------------- checks


def _check_traversal(mod, env):
    users_dir = env["users_dir"]
    payloads = [
        "../../etc/passwd",
        "../" + os.path.basename(users_dir) + "_evil/secret",
        env["canary_file"],
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
    ]
    plain = _relpath(env["canary_file"], users_dir)
    if plain and plain.startswith(".."):
        payloads.append(plain)

    problems = []
    for payload in payloads:
        try:
            value = mod.get_user_file(payload)
        except Exception:  # noqa: BLE001 - refusing the name outright is a valid fix
            continue
        if CANARY_MARKER in _payload_text(value):
            problems.append(f"{payload!r} returned content from outside USERS_DIR")
        elif _looks_like_path(value) and not _contained(value, users_dir):
            problems.append(f"{payload!r} returned a path outside USERS_DIR: {value!r}")
    if problems:
        return False, "; ".join(problems)
    return True, ""


def _check_user_happy_path(mod, env):
    value = mod.get_user_file("alice")
    text = _payload_text(value)
    if ALICE_MARKER not in text:
        return False, f"expected the alice profile, got {value!r}{env['note']}"
    if _looks_like_path(value) and not _contained(value, env["users_dir"]):
        return False, f"the alice path is not inside USERS_DIR: {value!r}"
    return True, ""


def _check_sql_injection(mod, env):
    payloads = ["admin'; DROP TABLE users;--", "' OR '1'='1"]
    problems = []
    for payload in payloads:
        try:
            query = mod.build_query("users", payload)
        except Exception as exc:  # noqa: BLE001 - a valid table name must still build
            problems.append(f"{payload!r}: build_query raised {type(exc).__name__}")
            continue
        ok, why = _params_carry_payload(query, payload)
        if not ok:
            problems.append(f"{payload!r}: {why}")
            continue
        rows, err = _run_query(query, "users")
        if rows is None:
            problems.append(f"{payload!r}: sqlite3 could not execute it ({err})")
        elif err:
            problems.append(f"{payload!r}: {err}")
        elif rows:
            problems.append(f"{payload!r}: selected {len(rows)} row(s), expected 0")
    if problems:
        return False, "; ".join(problems)
    return True, ""


def _check_sql_valid(mod, env):
    query = mod.build_query("users", "alice")
    rows, err = _run_query(query, "users")
    if rows is None:
        return False, f"sqlite3 could not execute it ({err})"
    if err:
        return False, err
    flat = [_as_text(c) for row in rows for c in row]
    if len(rows) != 1 or "alice" not in flat:
        return False, f"expected exactly the alice row, got {rows!r}"
    # Vary the table so a solution that hardcodes "users" and silently discards its first
    # argument is caught. Both call sites previously passed "users", so dropping the parameter
    # entirely scored full marks: the check could not see a signature it never exercised.
    other = mod.build_query("members", "alice")
    rows, err = _run_query(other, "members")
    if rows is None:
        return False, f"build_query ignores its table argument, or produced invalid SQL: {err}"
    if err:
        return False, err
    flat = [_as_text(c) for row in rows for c in row]
    if len(rows) != 1 or "alice" not in flat:
        return False, (f"querying the 'members' table returned {rows!r}; build_query must use "
                       "the table it is given rather than a hardcoded name")
    return True, ""


def _params_carry_payload(query, payload):
    """A (sql, params) pair must not carry the raw user value in its SQL text.

    That is the whole structural gate: wrapping the unchanged f-string in a 2-tuple is
    caught here. Everything else is left to execution, which is stricter than any shape
    test. In particular the payload is NOT required to appear verbatim in params, so
    escaping the value and then binding it also passes.
    """
    if not isinstance(query, (tuple, list)):
        return True, ""  # a plain string is judged by execution alone
    if len(query) != 2:
        return False, f"expected a (sql, params) pair, got {len(query)} element(s)"
    if not isinstance(query[0], str):
        return False, "the first element of the pair is not SQL text"
    if payload in query[0]:
        return False, "the payload is interpolated into the SQL text instead of bound"
    return True, ""


def _run_query(query, table):
    """Execute against a real table. Returns (rows, error); rows is None when it will not run."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, username TEXT)")
        conn.executemany(f"INSERT INTO {table} (username) VALUES (?)", [("alice",), ("bob",)])
        conn.commit()
        if isinstance(query, (tuple, list)) and len(query) == 2:
            sql = _sqlite_placeholders(_as_text(query[0]))
            cur = conn.execute(sql, query[1])
        else:
            cur = conn.execute(_as_text(query))
        rows = cur.fetchall()
        remaining = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return rows, ("" if remaining == 2 else f"the {table} table no longer holds its 2 rows")
    except Exception as exc:  # noqa: BLE001 - report why, the caller decides
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        conn.close()


def _sqlite_placeholders(sql):
    """Accept other drivers' placeholder styles so the dialect is not the thing under test."""
    import re

    sql = re.sub(r"%\((\w+)\)s", r":\1", sql)
    return sql.replace("%s", "?")


def _recoverable_forms(plaintext):
    """Trivially reversible renderings of the password.

    Encoding is not hashing. A module that stores base64 of the password has not protected it,
    and base64 is a realistic accidental answer on a scenario whose stated flaw is "no hashing",
    so it must not pass. Code points are included because they are equally reversible.
    """
    import base64

    raw = plaintext.encode("utf-8")
    forms = {
        plaintext,
        plaintext[::-1],
        raw.hex(),
        raw.hex().upper(),
        base64.b64encode(raw).decode(),
        base64.b64encode(raw).decode().rstrip("="),
        base64.urlsafe_b64encode(raw).decode(),
        base64.urlsafe_b64encode(raw).decode().rstrip("="),
        base64.b32encode(raw).decode(),
    }
    return forms, tuple(raw)


def _reversible_hit(mod):
    """Find any reversible rendering of the password anywhere in the module's constants.

    This does not need to locate "the credential store", which is what made the previous version
    escapable: it inspects everything the module holds.
    """
    forms, codepoints = _recoverable_forms(PLAINTEXT)
    for name, value in sorted(vars(mod).items()):
        if name.startswith("__"):
            continue
        flat = list(_flatten(value))
        for item in flat:
            if isinstance(item, bytes):
                item = item.decode("utf-8", "replace")
            if isinstance(item, str) and item.strip() in forms:
                return f"{name} holds a reversibly encoded copy of the password"
        ints = tuple(i for i in flat if isinstance(i, int) and not isinstance(i, bool))
        if codepoints and len(ints) >= len(codepoints):
            joined = "".join(chr(i) for i in ints if 0 <= i < 0x110000)
            if PLAINTEXT in joined:
                return f"{name} holds the password as recoverable character codes"
    return ""


def _check_password_storage(mod, env):
    reversible = _reversible_hit(mod)
    if reversible:
        return False, reversible
    stored = _stored_credentials(mod, "alice")
    if stored is None:
        # Fail closed. Returning True here inferred the property from the absence of evidence,
        # which a module could arrange simply by naming things unusually: it passed by default
        # rather than by proof. On a security check, "cannot verify" is not "verified".
        return False, (
            "cannot locate the stored credential, so hashing at rest could not be verified. "
            "Expose it via a module-level mapping keyed by username, or a helper whose name "
            "mentions lookup/credential/password/hash/digest, so this property is checkable"
        )
    for value in stored:
        for item in _flatten(value):
            if isinstance(item, bytes):
                item = item.decode("utf-8", "replace")
            if isinstance(item, str) and item == PLAINTEXT:
                return False, "the stored credential is the plaintext password"
    for value in stored:
        candidate = value.decode("utf-8", "replace") if isinstance(value, bytes) else value
        if not isinstance(candidate, str):
            continue
        try:
            accepted = bool(mod.authenticate("alice", candidate))
        except Exception:  # noqa: BLE001 - raising is not accepting
            accepted = False
        if accepted:
            return False, "the stored credential is itself accepted as the password"
    return True, ""


def _stored_credentials(mod, user):
    """What the module has on file for `user`, or None when nothing is reachable."""
    found = []
    for name, value in sorted(vars(mod).items()):
        if name.startswith("__"):
            continue
        if isinstance(value, dict):
            if user in value:
                found.append(value[user])
            continue
        low = name.lower()
        keywords = ("lookup", "credential", "password", "hash", "secret", "stored", "digest")
        if callable(value) and any(k in low for k in keywords):
            try:
                result = value(user)
            except Exception:  # noqa: BLE001 - wrong arity just means this is not the store
                continue
            if result is not None:
                found.append(result)
    return found or None


def _flatten(value, depth=0):
    if depth > 3:
        return
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _flatten(item, depth + 1)
    else:
        yield value


def _has_constant(mod, needle):
    codes, values = [], []
    for name, value in vars(mod).items():
        if name.startswith("__"):
            continue
        code = getattr(value, "__code__", None)
        if code is not None:
            codes.append(code)
        else:
            values.append(value)
    while codes:
        for const in codes.pop().co_consts:
            if hasattr(const, "co_consts"):
                codes.append(const)
            else:
                values.append(const)
    budget = 5000
    while values and budget > 0:
        budget -= 1
        value = values.pop()
        if isinstance(value, str) and value == needle:
            return True
        if isinstance(value, bytes) and value == needle.encode():
            return True
        if isinstance(value, dict):
            values.extend(value.keys())
            values.extend(value.values())
        elif isinstance(value, (list, tuple, set, frozenset)):
            values.extend(value)
    return False


def _check_auth_behavior(mod, env):
    problems = []
    for user, password in (("alice", PLAINTEXT), ("bob", "hunter2")):
        try:
            if not mod.authenticate(user, password):
                problems.append(f"rejected the valid credentials for {user!r}")
        except Exception as exc:  # noqa: BLE001 - valid credentials must not raise
            problems.append(f"{user!r} raised {type(exc).__name__}")
    wrong = [
        ("alice", "wrong-password"),
        ("alice", ""),
        ("alice", "PASSWORD123"),
        ("alice", PLAINTEXT + "x"),
        ("carol", PLAINTEXT),
    ]
    for user, password in wrong:
        try:
            accepted = bool(mod.authenticate(user, password))
        except Exception:  # noqa: BLE001 - refusing by raising is still refusing
            accepted = False
        if accepted:
            problems.append(f"accepted {user!r} with {password!r}")
    if problems:
        return False, "; ".join(problems)
    return True, ""


def _check_config_refusal(mod, env):
    canary = env["canary_config"]
    problems = []
    # 1. An absolute path to a file that really exists outside the allowed directory. The
    #    canary is there, so FileNotFoundError means the probe was inconclusive: a failure.
    try:
        value = mod.get_config(canary)
    except FileNotFoundError:
        problems.append("FileNotFoundError for a canary that exists, so nothing was proven")
    except Exception:  # noqa: BLE001 - refusing the path is the fix
        pass
    else:
        if CANARY_MARKER in _payload_text(value):
            problems.append("the absolute path outside the allowed directory was read")
    # 2. The same file reached by traversal.
    relative = _relpath(canary, os.path.dirname(env["config_path"]))
    if relative and relative.startswith(".."):
        try:
            value = mod.get_config(relative)
        except Exception:  # noqa: BLE001 - refusing is the fix
            pass
        else:
            if CANARY_MARKER in _payload_text(value):
                problems.append(f"traversal {relative!r} reached outside the allowed directory")
    if problems:
        return False, "; ".join(problems)
    return True, ""


def _check_config_happy_path(mod, env):
    config_path = env["config_path"]
    attempts = [(config_path,), (os.path.basename(config_path),), ()]
    errors = []
    for args in attempts:
        try:
            value = mod.get_config(*args)
        except Exception as exc:  # noqa: BLE001 - try the next accepted shape
            errors.append(f"{args!r}: {type(exc).__name__}")
            continue
        if CONFIG_MARKER in _payload_text(value):
            return True, ""
        errors.append(f"{args!r}: returned {value!r}")
    return False, f"no call returned the allowed config: {'; '.join(errors)}{env['note']}"


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
