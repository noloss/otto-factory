"""Tests for factory/github_client.py — pure helpers and error handling."""
import pytest
from unittest.mock import MagicMock, patch

from factory.github_client import merge_labels
import factory.github_client as ghc


class TestMergeLabels:
    def test_adds_extra_label(self):
        assert "agent-todo" in merge_labels([], "agent-todo")

    def test_deduplicates(self):
        result = merge_labels(["agent-todo", "bug"], "agent-todo")
        assert result.count("agent-todo") == 1

    def test_preserves_existing_labels(self):
        result = merge_labels(["bug", "enhancement"], "agent-todo")
        assert "bug" in result
        assert "enhancement" in result
        assert "agent-todo" in result

    def test_multiple_extras(self):
        result = merge_labels(["bug"], "agent-todo", "review-needed")
        assert all(l in result for l in ["bug", "agent-todo", "review-needed"])

    def test_empty_inputs(self):
        assert merge_labels([], "agent-todo") == ["agent-todo"]


class TestUrlParsing:
    """create_issue and create_pr extract an int from gh's output URL.
    Verify they raise RuntimeError on unexpected output."""

    def _run_result(self, stdout, returncode=0):
        m = MagicMock()
        m.stdout = stdout
        m.returncode = returncode
        return m

    def test_create_issue_bad_url_raises(self):
        with patch.object(ghc, "_run", return_value=self._run_result("not-a-url\n")):
            with patch.object(ghc, "ensure_labels"):
                with pytest.raises(RuntimeError, match="unexpected output"):
                    ghc.create_issue("ms", "title", "body", ["agent-todo"])

    def test_create_pr_bad_url_raises(self):
        with patch.object(ghc, "_run", return_value=self._run_result("bad\n")):
            with patch.object(ghc, "ensure_labels"):
                with pytest.raises(RuntimeError, match="unexpected output"):
                    ghc.create_pr("title", "body", "feature/branch")

    def test_create_issue_valid_url(self):
        url = "https://github.com/owner/repo/issues/42\n"
        with patch.object(ghc, "_run", return_value=self._run_result(url)):
            with patch.object(ghc, "ensure_labels"):
                assert ghc.create_issue("ms", "title", "body", ["agent-todo"]) == 42

    def test_create_pr_valid_url(self):
        url = "https://github.com/owner/repo/pull/7\n"
        with patch.object(ghc, "_run", return_value=self._run_result(url)):
            with patch.object(ghc, "ensure_labels"):
                assert ghc.create_pr("title", "body", "feature/branch") == 7
