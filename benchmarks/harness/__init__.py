"""Programmatic Verification Harness for Realistic SWE Benchmarks."""
from .blast_radius import audit_blast_radius
from .comment_auditor import audit_comment_noise
from .diff_ruler import audit_diff_and_yagni
from .git_auditor import audit_git_cleanliness
from .hash_guard import compute_file_sha256, verify_test_integrity
from .runner import BenchmarkRunner, BenchmarkSuiteResult, ScenarioResult

__all__ = [
    "compute_file_sha256",
    "verify_test_integrity",
    "audit_blast_radius",
    "audit_diff_and_yagni",
    "audit_comment_noise",
    "audit_git_cleanliness",
    "BenchmarkRunner",
    "BenchmarkSuiteResult",
    "ScenarioResult",
]
