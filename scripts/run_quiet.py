#!/usr/bin/env python3
"""Run quiet command wrapper for AutoEvolve.

Executes a command, logs full stdout/stderr to .autoevolve_last_run.log, and prints a concise
summary so a long build or test log does not consume an agent's context window.

Usage:
    python scripts/run_quiet.py -- <command> [args...]      # argv form, always correct
    python scripts/run_quiet.py -- pytest -k "not slow"

The arguments after `--` are passed to the child EXACTLY as received. This wrapper never
re-parses them into a shell string, because it is the verification step of a keep-or-revert
loop: its exit code decides whether work is kept or thrown away, so it must not be able to
misreport. An earlier version re-split a single quoted string with
`shlex.split(..., posix=(sys.platform != "win32"))`, which on Windows kept the quote characters
and made `python -c "import sys; sys.exit(1)"` report SUCCESS while making a valid
`pytest -k "not slow"` report FAILED. A wrong signal there means a passing experiment is
reverted or a failing one is committed.
"""
import argparse
import os
import shlex
import subprocess
import sys
import time

LOG_FILE = ".autoevolve_last_run.log"
DEFAULT_TIMEOUT = 1800
SUMMARY_LINES = 10


def parse_cmd_args(raw_args):
    """Normalize the command into an argv list without ever re-splitting a caller's argv.

    A list is passed through verbatim. A bare string has no argv form, so it is split with
    POSIX rules for the convenience of direct Python callers; command-line users should use the
    `--` argv form, which cannot be misparsed.
    """
    if isinstance(raw_args, str):
        return shlex.split(raw_args)
    if isinstance(raw_args, list):
        return [str(arg) for arg in raw_args]
    raise TypeError(f"Command input must be str or list of str, got {type(raw_args).__name__}")


def _exit_code(returncode: int) -> int:
    """Map a signal death to the shell convention so a caller can tell what happened.

    A negative returncode passed straight to sys.exit surfaces as 256 + n (for example -9
    becomes 247), which is indistinguishable from an ordinary failure exit code.
    """
    return min(128 + abs(returncode), 255) if returncode < 0 else returncode


def _write_log(log_path, cmd_str, returncode, elapsed, stdout, stderr):
    with open(log_path, "w", encoding="utf-8", errors="replace") as handle:
        handle.write(f"=== Command: {cmd_str} ===\n")
        handle.write(f"=== Return Code: {returncode} ===\n")
        handle.write(f"=== Duration: {elapsed:.3f}s ===\n\n")
        handle.write("--- STDOUT ---\n")
        handle.write(stdout or "")
        handle.write("\n--- STDERR ---\n")
        handle.write(stderr or "")


def _failure_tail(stdout: str, stderr: str) -> list[str]:
    """Show both streams on failure.

    Test runners write the actual assertion to stdout while stderr carries only deprecation
    noise, so an earlier stderr-first-else-stdout rule routinely hid the real reason.
    """
    lines = []
    for label, text in (("stdout", stdout), ("stderr", stderr)):
        body = (text or "").strip().splitlines()
        if body:
            lines.append(f"--- {label} (last {min(len(body), SUMMARY_LINES)}) ---")
            lines.extend(body[-SUMMARY_LINES:])
    return lines


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    argv = sys.argv[1:]
    timeout = DEFAULT_TIMEOUT
    if "--" in argv:
        idx = argv.index("--")
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
        known, _ = parser.parse_known_args(argv[:idx])
        timeout = known.timeout
        cmd_args = argv[idx + 1:]
    else:
        cmd_args = argv

    if not cmd_args:
        print("Usage: python scripts/run_quiet.py -- <command> [args...]", file=sys.stderr)
        return 64

    start = time.perf_counter()
    log_path = os.path.abspath(LOG_FILE)
    parsed_cmd = None

    try:
        parsed_cmd = parse_cmd_args(cmd_args)
        if not parsed_cmd:
            print("Usage: python scripts/run_quiet.py -- <command> [args...]", file=sys.stderr)
            return 64

        cmd_str = shlex.join(parsed_cmd)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        try:
            res = subprocess.run(
                parsed_cmd, shell=False, capture_output=True, text=True,
                encoding="utf-8", errors="replace", env=env, timeout=timeout,
            )
            stdout, stderr, returncode = res.stdout, res.stderr, res.returncode
        except subprocess.TimeoutExpired as expired:
            # Without this branch a non-exiting command hangs forever having written no log.
            elapsed = time.perf_counter() - start
            stdout, stderr = expired.stdout or "", expired.stderr or ""
            _write_log(log_path, cmd_str, 124, elapsed, stdout, f"{stderr}\nTIMEOUT after {timeout}s")
            print(f"[run_quiet] FAILED (timeout after {timeout}s) | cmd: '{cmd_str}' | Log: {LOG_FILE}",
                  file=sys.stderr)
            return 124

        elapsed = time.perf_counter() - start
        _write_log(log_path, cmd_str, returncode, elapsed, stdout, stderr)

        status_str = "SUCCESS" if returncode == 0 else f"FAILED (exit {returncode})"
        print(f"[run_quiet] {status_str} in {elapsed:.3f}s | cmd: '{cmd_str}' | Log: {LOG_FILE}")

        if returncode != 0:
            print("  Error summary:")
            for line in _failure_tail(stdout, stderr):
                print(f"    {line}")
        elif (stdout or "").strip():
            print("  Output tail (last 3 lines):")
            for line in stdout.strip().splitlines()[-3:]:
                print(f"    {line}")

        return _exit_code(returncode)

    except (FileNotFoundError, OSError, ValueError) as err:
        elapsed = time.perf_counter() - start
        exit_code = 127 if isinstance(err, FileNotFoundError) else 1
        if parsed_cmd:
            cmd_str = shlex.join(parsed_cmd)
        elif isinstance(cmd_args, list):
            cmd_str = " ".join(cmd_args)
        else:
            cmd_str = str(cmd_args)

        err_msg = str(err)
        _write_log(log_path, cmd_str, exit_code, elapsed, "", err_msg)
        print(f"[run_quiet] FAILED (exit {exit_code}) in {elapsed:.3f}s | cmd: '{cmd_str}' | "
              f"Log: {LOG_FILE}", file=sys.stderr)
        print(f"    {err_msg}", file=sys.stderr)
        if isinstance(err, FileNotFoundError) and parsed_cmd and len(parsed_cmd) == 1 and " " in parsed_cmd[0]:
            # The most likely mistake now that argv is never re-split.
            print("  Hint: pass the command as separate arguments after `--`, not as one "
                  "quoted string:\n"
                  "    python scripts/run_quiet.py -- pytest -k \"not slow\"", file=sys.stderr)
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
