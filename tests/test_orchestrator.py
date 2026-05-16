"""Tests for factory/orchestrator.py — rate-limit abort in run_milestone."""
import pytest
from unittest.mock import MagicMock, patch

from factory.llm_engine import RateLimitError
import factory.orchestrator as orch
import factory.github_client as ghc


class TestRunMilestoneRateLimitAbort:
    def _make_issue(self, number):
        return {"number": number, "title": f"Issue {number}", "body": "body", "labels": []}

    def test_stops_on_rate_limit_does_not_process_remaining(self):
        issues = [self._make_issue(1), self._make_issue(2), self._make_issue(3)]
        processed = []

        def fake_process(number, milestone, _depth=0):
            processed.append(number)
            if number == 1:
                raise RateLimitError("rate limited")

        with patch.object(ghc, "get_issues", return_value=issues):
            with patch.object(orch, "process_issue", side_effect=fake_process):
                orch.run_milestone("Release 1")

        assert processed == [1], "Should stop after the first rate-limit"

    def test_returns_cleanly_without_raising(self):
        issues = [self._make_issue(1)]
        with patch.object(ghc, "get_issues", return_value=issues):
            with patch.object(orch, "process_issue", side_effect=RateLimitError("x")):
                orch.run_milestone("Release 1")  # must not raise

    def test_completes_all_issues_when_no_rate_limit(self):
        issues = [self._make_issue(1), self._make_issue(2)]
        processed = []
        with patch.object(ghc, "get_issues", return_value=issues):
            with patch.object(orch, "process_issue", side_effect=lambda n, m, **kw: processed.append(n)):
                orch.run_milestone("Release 1")
        assert processed == [1, 2]

    def test_no_issues_returns_early(self):
        with patch.object(ghc, "get_issues", return_value=[]):
            orch.run_milestone("Release 1")  # should not raise or call process_issue


class TestCleanupCalledAfterLGTM:
    """After a LGTM verdict, process_issue must call coder.cleanup_after_merge."""

    def _make_issue(self, number):
        return {"number": number, "title": f"Issue {number}", "body": "body", "labels": []}

    def test_cleanup_called_on_lgtm(self):
        with patch.object(ghc, "get_issue", return_value=self._make_issue(1)):
            with patch.object(ghc, "is_issue_done", return_value=False):
                with patch.object(ghc, "find_open_pr_for_issue", return_value=None):
                    with patch.object(orch, "run_tests", return_value=(True, "")):
                        import factory.coder as coder_mod
                        with patch.object(coder_mod, "run_issue", return_value=10):
                            with patch.object(coder_mod, "cleanup_after_merge") as mock_cleanup:
                                import factory.reviewer as rev_mod
                                with patch.object(rev_mod, "review_pr", return_value=("LGTM", "")):
                                    orch.process_issue(1, "Release 1")

        mock_cleanup.assert_called_once_with(1)

    def test_cleanup_not_called_when_reviewer_rejects(self):
        with patch.object(ghc, "get_issue", return_value=self._make_issue(1)):
            with patch.object(ghc, "is_issue_done", return_value=False):
                with patch.object(ghc, "find_open_pr_for_issue", return_value=None):
                    with patch.object(ghc, "update_label", return_value=None):
                        with patch.object(orch, "run_tests", return_value=(True, "")):
                            import factory.coder as coder_mod
                            with patch.object(coder_mod, "run_issue", return_value=10):
                                with patch.object(coder_mod, "cleanup_after_merge") as mock_cleanup:
                                    import factory.reviewer as rev_mod
                                    with patch.object(rev_mod, "review_pr", return_value=("CHANGES_REQUESTED", "fix it")):
                                        orch.process_issue(1, "Release 1")

        mock_cleanup.assert_not_called()
