"""Safe subprocess execution passing array arguments without shell=True."""
from __future__ import annotations

import subprocess
from typing import List, Tuple


def safe_run_command(cmd_args: List[str], cwd: str = ".") -> Tuple[int, str, str]:
    """Execute a system command safely without shell expansion or parameter injection."""
    if not cmd_args or not isinstance(cmd_args, list):
        raise ValueError("cmd_args must be a non-empty list of strings")

    for arg in cmd_args:
        if not isinstance(arg, str):
            raise TypeError("All command arguments must be strings")

    try:
        proc = subprocess.run(
            cmd_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as exc:
        return -1, "", str(exc)
