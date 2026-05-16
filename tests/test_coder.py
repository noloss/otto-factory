"""Tests for pure helpers in factory/coder.py."""
from unittest.mock import MagicMock, patch, call

import factory.coder as coder
import factory.github_client as ghc
from factory.coder import _slug, _parse_count


class TestSlug:
    def test_lowercases(self):
        assert _slug("Hello World") == "hello-world"

    def test_strips_special_chars(self):
        assert _slug("Fix: auth/login bug!") == "fix-auth-login-bug"

    def test_caps_at_40_chars(self):
        assert len(_slug("a" * 50)) == 40

    def test_strips_leading_trailing_dashes(self):
        slug = _slug("  hello  ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_replaces_spaces_with_dash(self):
        assert _slug("add user login") == "add-user-login"

    def test_collapses_multiple_separators(self):
        assert _slug("fix--double  dash") == "fix-double-dash"


class TestParseCount:
    def _result(self, stdout, returncode=0):
        m = MagicMock()
        m.stdout = stdout
        m.returncode = returncode
        return m

    def test_returns_integer_on_success(self):
        assert _parse_count(self._result("3\n")) == 3

    def test_returns_zero_on_nonzero_returncode(self):
        assert _parse_count(self._result("3\n", returncode=1)) == 0

    def test_returns_zero_on_empty_stdout(self):
        assert _parse_count(self._result("")) == 0

    def test_strips_whitespace(self):
        assert _parse_count(self._result("  7  \n")) == 7


class TestCleanupAfterMerge:
    def _git_ok(self, *_args, **_kwargs):
        r = MagicMock()
        r.returncode = 0
        r.stdout = ""
        r.stderr = ""
        return r

    def _git_fail(self, *_args, **_kwargs):
        r = MagicMock()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "error"
        return r

    def test_checks_out_main_pulls_and_deletes_branch(self):
        git_calls = []

        def fake_git(args, check=True):
            git_calls.append(args)
            return self._git_ok()

        with patch.object(ghc, "get_issue", return_value={"title": "Add login page", "body": ""}):
            with patch.object(coder, "_git", side_effect=fake_git):
                coder.cleanup_after_merge(7)

        assert ["checkout", "main"] in git_calls
        assert ["pull", "origin", "main"] in git_calls
        assert ["branch", "-d", "feature/issue-7-add-login-page"] in git_calls

    def test_force_deletes_when_soft_delete_fails(self):
        git_calls = []

        def fake_git(args, check=True):
            git_calls.append(args)
            if args[:2] == ["branch", "-d"]:
                return self._git_fail()
            return self._git_ok()

        with patch.object(ghc, "get_issue", return_value={"title": "Add login page", "body": ""}):
            with patch.object(coder, "_git", side_effect=fake_git):
                coder.cleanup_after_merge(7)

        assert ["branch", "-D", "feature/issue-7-add-login-page"] in git_calls

    def test_does_not_raise_when_git_fails(self):
        with patch.object(ghc, "get_issue", return_value={"title": "Add login", "body": ""}):
            with patch.object(coder, "_git", side_effect=Exception("git exploded")):
                coder.cleanup_after_merge(5)  # must not raise
