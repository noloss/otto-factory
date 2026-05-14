import sys
from . import github_client as gh
from .llm_engine import run_claude, READ_ONLY_TOOLS
from .config import PROMPTS_DIR

REVIEWER_SCHEMA = {
    "type": "object",
    "required": ["approve", "findings"],
    "properties": {
        "approve":  {"type": "boolean"},
        "findings": {"type": "array", "items": {"type": "string"}},
    },
}

_DIFF_LIMIT = 20_000


def review_pr(pr_number):
    """
    Review a PR diff and return (verdict, comment).
    verdict is "LGTM" or "CHANGES_REQUESTED".
    """
    diff = gh.get_diff(pr_number)

    if not diff or not diff.strip():
        return "CHANGES_REQUESTED", "Empty diff — nothing was implemented."

    if len(diff) > _DIFF_LIMIT:
        diff = diff[:_DIFF_LIMIT] + "\n[diff truncated]"

    system = (PROMPTS_DIR / "reviewer.txt").read_text()
    prompt = f"Review this pull request diff:\n\n{diff}"

    print(f"[reviewer] Reviewing PR #{pr_number}…")
    ok, result = run_claude(
        prompt,
        system=system,
        schema=REVIEWER_SCHEMA,
        tools=READ_ONLY_TOOLS,
        timeout=180,
    )

    if not ok or result is None:
        msg = "Reviewer could not produce a structured response — treating as changes requested."
        print(f"[reviewer] {msg}", file=sys.stderr)
        return "CHANGES_REQUESTED", msg

    approved = result.get("approve", False)
    findings = result.get("findings", [])
    findings_text = "\n".join(f"- {f}" for f in findings) if findings else ""

    if approved:
        comment = "✅ LGTM" + (f"\n\n{findings_text}" if findings_text else "")
        gh.post_comment(pr_number, comment)
        gh.merge_pr(pr_number)
        print(f"[reviewer] PR #{pr_number} approved and merged.")
        return "LGTM", ""
    else:
        comment = f"🔴 CHANGES REQUESTED\n\n{findings_text}"
        gh.post_comment(pr_number, comment)
        # Find the issue number from the PR body and update labels
        pr_info = _get_pr_info(pr_number)
        if pr_info:
            issue_num = _extract_issue_number(pr_info.get("body", ""))
            if issue_num:
                gh.update_label(issue_num, add=["revision-needed"], remove=["review-needed"])
        print(f"[reviewer] PR #{pr_number} — changes requested.")
        return "CHANGES_REQUESTED", findings_text


def _get_pr_info(pr_number):
    import json
    result = gh._run(["pr", "view", str(pr_number), "--json", "body,title"], check=False)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None


def _extract_issue_number(body):
    import re
    m = re.search(r"Closes #(\d+)", body or "")
    return int(m.group(1)) if m else None
