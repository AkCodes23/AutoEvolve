"""Fail-closed Docker sandbox for evaluating untrusted model-generated code.

The profiler deliberately executes a model's proposed source file through a scenario grader.
That source must never run in the host repository or inherit host credentials. This module
requires a locally available, digest-pinned Docker image and starts it without network,
Linux capabilities, writable root filesystem, or environment forwarding.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


IMAGE_ENV = "AUTOEVOLVE_EVAL_IMAGE"


class SandboxUnavailable(RuntimeError):
    """Raised when the required isolated execution environment is not ready."""


@dataclass(frozen=True)
class SandboxResult:
    stdout: str
    stderr: str
    returncode: int


def _image_reference() -> str:
    image = os.environ.get(IMAGE_ENV, "").strip()
    if not image:
        raise SandboxUnavailable(
            f"Set {IMAGE_ENV} to a locally pulled digest-pinned Python image before profiling."
        )
    if "@sha256:" not in image:
        raise SandboxUnavailable(
            f"{IMAGE_ENV} must be digest-pinned (for example, python:3.12-alpine@sha256:...)."
        )
    return image


def _docker() -> str:
    docker = shutil.which("docker")
    if not docker:
        raise SandboxUnavailable("Docker is required for profiling untrusted model output.")
    return docker


def ensure_ready() -> str:
    """Return the configured image only when Docker can inspect it without pulling."""
    docker = _docker()
    image = _image_reference()
    probe = subprocess.run(
        [docker, "image", "inspect", image], capture_output=True, text=True, timeout=20
    )
    if probe.returncode:
        raise SandboxUnavailable(
            f"Sandbox image is not available locally: {image}. Pull and verify it before running."
        )
    return image


def run_python(workspace: str, script: str, timeout: int = 60) -> SandboxResult:
    """Run a grader in a read-only, no-network container mounted only to `workspace`."""
    docker = _docker()
    image = ensure_ready()
    command = [
        docker,
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "256m",
        "--cpus",
        "0.5",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16m",
        "--mount",
        f"type=bind,source={os.path.abspath(workspace)},target=/workspace,readonly",
        "--workdir",
        "/workspace",
        image,
        "python",
        "-I",
        "-B",
        "-c",
        script,
        "/workspace",
    ]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        return SandboxResult(exc.stdout or "", exc.stderr or "sandbox timeout", 124)
    return SandboxResult(completed.stdout, completed.stderr, completed.returncode)
