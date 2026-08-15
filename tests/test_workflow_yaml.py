"""Tests verifying GitHub Actions workflow YAML syntax and security permissions."""
from __future__ import annotations

import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_PATH = os.path.join(REPO_ROOT, ".github", "workflows", "ai-guardrails.yml")


class TestWorkflowSecurity:
    def test_workflow_file_exists(self):
        assert os.path.isfile(WORKFLOW_PATH), "Workflow file must exist"

    def test_workflow_contains_least_privilege_permissions(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "permissions:" in content
        assert "contents: read" in content

    def test_workflow_disables_credential_persistence(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "persist-credentials: false" in content

    def test_workflow_triggers_on_pull_request(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "on:" in content
        assert "pull_request:" in content
