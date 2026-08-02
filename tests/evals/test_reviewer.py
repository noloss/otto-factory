from pathlib import Path
from unittest.mock import patch
import pytest

from factory.reviewer import review_pr
from tests.evals.reviewer_cases import CASES

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.llm
@pytest.mark.parametrize("case", CASES, ids=[c["description"] for c in CASES])
def test_reviewer_eval(case):
    diff = (FIXTURES_DIR / case["fixture"]).read_text()

    with (
        patch("factory.reviewer.gh.get_diff", return_value=diff),
        patch("factory.reviewer.gh.post_comment"),
        patch("factory.reviewer.gh.merge_pr", return_value=True),
    ):
        verdict, findings_text = review_pr(pr_number=99)

    assert verdict == case["expect_verdict"], (
        f"[{case['description']}] "
        f"expected {case['expect_verdict']!r}, got {verdict!r}\n"
        f"findings: {findings_text}"
    )

    findings_lower = findings_text.lower()
    for keyword in case["findings_contain"]:
        if keyword in findings_lower:
            return  # any single match is sufficient

    if case["findings_contain"]:
        pytest.fail(
            f"[{case['description']}] "
            f"findings did not contain any of {case['findings_contain']!r}\n"
            f"actual findings: {findings_text}"
        )
