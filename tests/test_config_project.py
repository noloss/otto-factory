"""Tests for the two-layer config loading introduced in Part 2.

Each test that involves config.py loading uses a subprocess so we get a clean
module state — config.py runs validation at import time and cannot be re-imported.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

_FACTORY_ROOT = Path(__file__).parent.parent
_PY = sys.executable


def _run(code, *, env_overrides=None, project_dir=None):
    """Run a python snippet in a subprocess with controlled env."""
    env = {k: v for k, v in os.environ.items()}
    if env_overrides:
        env.update(env_overrides)
    if project_dir:
        env["OTTO_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [_PY, "-c", code],
        cwd=str(_FACTORY_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )


class TestProjectDirDiscovery:
    def test_otto_file_in_project_dir_is_loaded(self, tmp_path):
        (tmp_path / ".otto").write_text("GITHUB_REPO=test-owner/project-a\n")
        result = _run(
            "from factory.config import GITHUB_REPO; print(GITHUB_REPO)",
            project_dir=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "test-owner/project-a"

    def test_target_dir_explicit_override_wins(self, tmp_path):
        custom_target = tmp_path / "custom"
        (tmp_path / ".otto").write_text(
            f"GITHUB_REPO=owner/repo\nTARGET_DIR={custom_target}\n"
        )
        result = _run(
            "from factory.config import TARGET_DIR; print(TARGET_DIR)",
            project_dir=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(custom_target)

    def test_missing_otto_file_falls_back_to_env_file(self, tmp_path):
        # No .otto in tmp_path — GITHUB_REPO comes from OTTO_FACTORY .env or env var
        result = _run(
            "from factory.config import GITHUB_REPO; print(GITHUB_REPO)",
            project_dir=tmp_path,
            env_overrides={"GITHUB_REPO": "owner/fallback-repo"},
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "owner/fallback-repo"

    def test_otto_overrides_env_var(self, tmp_path):
        (tmp_path / ".otto").write_text("GITHUB_REPO=otto-owner/otto-repo\n")
        result = _run(
            "from factory.config import GITHUB_REPO; print(GITHUB_REPO)",
            project_dir=tmp_path,
            env_overrides={"GITHUB_REPO": "env-owner/env-repo"},
        )
        assert result.returncode == 0, result.stderr
        # .otto uses override=True, so it wins over the pre-set env var
        assert result.stdout.strip() == "otto-owner/otto-repo"

    def test_missing_github_repo_shows_project_path_in_error(self, tmp_path):
        result = _run(
            "from factory import config",
            project_dir=tmp_path,
            env_overrides={"GITHUB_REPO": ""},
        )
        assert result.returncode != 0
        assert str(tmp_path) in result.stderr


class TestSourceGlobDefault:
    def test_source_glob_overridable_in_otto(self, tmp_path):
        (tmp_path / ".otto").write_text("GITHUB_REPO=owner/repo\nSOURCE_GLOB=.\n")
        result = _run(
            "from factory.config import SOURCE_GLOB; print(SOURCE_GLOB)",
            project_dir=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "."
