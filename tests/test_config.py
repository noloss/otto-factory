"""Tests for factory/config.py."""
import ast
import os
import sys
import subprocess
from pathlib import Path
import pytest

_FACTORY_ROOT = Path(__file__).parent.parent


def _load_parse_fn():
    """Extract _parse_github_repo from source without triggering module-level side-effects."""
    src = (_FACTORY_ROOT / "factory" / "config.py").read_text()
    tree = ast.parse(src)
    fn_src = "\n".join(
        ast.get_source_segment(src, node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_parse_github_repo"
    )
    ns = {}
    exec(fn_src, ns)
    return ns["_parse_github_repo"]


_parse = _load_parse_fn()


class TestParseGithubRepo:
    def test_bare_owner_repo(self):
        assert _parse("owner/repo") == "owner/repo"

    def test_leading_slash(self):
        assert _parse("/owner/repo") == "owner/repo"

    def test_https_url(self):
        assert _parse("https://github.com/owner/repo") == "owner/repo"

    def test_https_url_trailing_slash(self):
        assert _parse("https://github.com/owner/repo/") == "owner/repo"

    def test_http_url(self):
        assert _parse("http://github.com/owner/repo") == "owner/repo"

    def test_empty_string(self):
        assert _parse("") == ""

    def test_none(self):
        assert _parse(None) == ""

    def test_whitespace_stripped(self):
        assert _parse("  owner/repo  ") == "owner/repo"


def _run_config_import(env_overrides):
    """Import factory.config in a subprocess with controlled environment."""
    env = {k: v for k, v in os.environ.items()}
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "from factory import config"],
        cwd=str(_FACTORY_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )


class TestConfigValidation:
    def test_invalid_coder_timeout_exits(self):
        result = _run_config_import({"GITHUB_REPO": "owner/repo", "CODER_TIMEOUT": "notanumber"})
        assert result.returncode != 0
        assert "invalid integer" in result.stderr.lower() or "CODER_TIMEOUT" in result.stderr

    def test_invalid_max_attempts_exits(self):
        result = _run_config_import({"GITHUB_REPO": "owner/repo", "MAX_ATTEMPTS": "xyz"})
        assert result.returncode != 0

    def test_missing_github_repo_exits(self):
        result = _run_config_import({"GITHUB_REPO": ""})
        assert result.returncode != 0
        assert "GITHUB_REPO" in result.stderr

    def test_valid_config_loads_cleanly(self):
        result = _run_config_import({"GITHUB_REPO": "owner/repo", "CODER_TIMEOUT": "300"})
        assert result.returncode == 0, result.stderr
