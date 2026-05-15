"""Tests for pure helpers in factory/coder.py."""
from unittest.mock import MagicMock

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
