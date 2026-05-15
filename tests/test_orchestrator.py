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
