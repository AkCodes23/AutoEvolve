#!/usr/bin/env python3
"""Run quiet command wrapper for AutoEvolve.

Executes a command, logs full stdout/stderr to .autoevolve_last_run.log,
and outputs a concise summary to stdout to conserve LLM context window tokens.
Usage:
    python scripts/run_quiet.py -- <command to execute>
"""
import os
import shlex
import subprocess
import sys
import time

LOG_FILE = ".autoevolve_last_run.log"


def parse_cmd_args(raw_args):
    """Safely parse command inputs (str or list of str) into an argument list."""
    posix_flag = (sys.platform != "win32")
    if isinstance(raw_args, str):
        return shlex.split(raw_args, posix=posix_flag)
    if isinstance(raw_args, list):
        if not raw_args:
            return []
        if len(raw_args) == 1 and isinstance(raw_args[0], str) and " " in raw_args[0]:
            return shlex.split(raw_args[0], posix=posix_flag)
        return [str(arg) for arg in raw_args]
    raise TypeError(f"Command input must be str or list of str, got {type(raw_args).__name__}")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    args = sys.argv[1:]
    if "--" in args:
        idx = args.index("--")
        cmd_args = args[idx + 1:]
    else:
        cmd_args = args

    if not cmd_args:
        print("Usage: python scripts/run_quiet.py -- <command>", file=sys.stderr)
        return 64

    start = time.perf_counter()
    log_path = os.path.abspath(LOG_FILE)

    try:
        parsed_cmd = parse_cmd_args(cmd_args)
        if not parsed_cmd:
            print("Usage: python scripts/run_quiet.py -- <command>", file=sys.stderr)
            return 64

        cmd_str = shlex.join(parsed_cmd)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(parsed_cmd, shell=False, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        elapsed = time.perf_counter() - start

        with open(log_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"=== Command: {cmd_str} ===\n")
            f.write(f"=== Return Code: {res.returncode} ===\n")
            f.write(f"=== Duration: {elapsed:.3f}s ===\n\n")
            f.write("--- STDOUT ---\n")
            f.write(res.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(res.stderr)

        stdout_lines = res.stdout.strip().splitlines() if res.stdout.strip() else []
        stderr_lines = res.stderr.strip().splitlines() if res.stderr.strip() else []

        status_str = "SUCCESS" if res.returncode == 0 else f"FAILED (exit {res.returncode})"
        print(f"[run_quiet] {status_str} in {elapsed:.3f}s | cmd: '{cmd_str}' | Log: {LOG_FILE}")

        if res.returncode != 0:
            print("  Error summary (last 10 lines):")
            tail = stderr_lines[-10:] if stderr_lines else stdout_lines[-10:]
            for line in tail:
                print(f"    {line}")
        elif stdout_lines:
            print("  Output tail (last 3 lines):")
            for line in stdout_lines[-3:]:
                print(f"    {line}")

        return res.returncode

    except (FileNotFoundError, OSError, ValueError) as err:
        elapsed = time.perf_counter() - start
        exit_code = 127 if isinstance(err, FileNotFoundError) else 1
        if 'parsed_cmd' in locals() and parsed_cmd:
            cmd_str = shlex.join(parsed_cmd)
        elif isinstance(cmd_args, list):
            cmd_str = " ".join(cmd_args)
        else:
            cmd_str = str(cmd_args)

        err_msg = str(err)
        with open(log_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"=== Command: {cmd_str} ===\n")
            f.write(f"=== Return Code: {exit_code} ===\n")
            f.write(f"=== Duration: {elapsed:.3f}s ===\n\n")
            f.write("--- STDOUT ---\n\n")
            f.write("--- STDERR ---\n")
            f.write(f"{err_msg}\n")

        print(f"[run_quiet] FAILED (exit {exit_code}) in {elapsed:.3f}s | cmd: '{cmd_str}' | Log: {LOG_FILE}", file=sys.stderr)
        print("  Error summary (last 10 lines):", file=sys.stderr)
        print(f"    {err_msg}", file=sys.stderr)
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
