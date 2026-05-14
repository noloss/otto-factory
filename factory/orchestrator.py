import shlex
import subprocess
import sys
from . import coder, reviewer
from . import github_client as gh
from .llm_engine import run_claude
from .config import TARGET_DIR, TEST_COMMAND, MAX_ATTEMPTS, PROMPTS_DIR

SPLITTER_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["milestone_title", "milestone_desc", "title", "body", "labels"],
        "properties": {
            "milestone_title": {"type": "string"},
            "milestone_desc":  {"type": "string"},
            "title":           {"type": "string"},
            "body":            {"type": "string"},
            "labels":          {"type": "array", "items": {"type": "string"}},
        },
    },
}


def run_tests():
    """Run the configured test command. Returns (passed: bool, output: str)."""
    if not TEST_COMMAND:
        return True, ""

    print(f"[orchestrator] Running tests: {TEST_COMMAND}")
    try:
        result = subprocess.run(
            shlex.split(TEST_COMMAND),
            cwd=TARGET_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        if passed:
            print("[orchestrator] Tests passed.")
        else:
            print(f"[orchestrator] Tests failed (exit {result.returncode}).", file=sys.stderr)
        return passed, output
    except subprocess.TimeoutExpired:
        msg = f"Test command timed out after 300s."
        print(f"[orchestrator] {msg}", file=sys.stderr)
        return False, msg
    except FileNotFoundError as e:
        msg = f"Test command not found: {e}"
        print(f"[orchestrator] {msg}", file=sys.stderr)
        return False, msg


def split_issue(issue_number):
    """Decompose an oversized issue into 2–4 sub-issues. Returns list of new issue numbers."""
    issue  = gh.get_issue(issue_number)
    system = (PROMPTS_DIR / "splitter.txt").read_text()
    prompt = f"Decompose this issue into 2–4 smaller sub-issues:\n\n{issue['body']}"

    print(f"[orchestrator] Splitting issue #{issue_number}…")
    ok, sub_issues = run_claude(prompt, system=system, schema=SPLITTER_SCHEMA, timeout=120)

    if not ok or not sub_issues:
        print(f"[orchestrator] Splitter failed for #{issue_number}", file=sys.stderr)
        return []

    created = []
    for sub in sub_issues:
        labels = list(set(sub.get("labels", []) + ["agent-todo"]))
        gh.ensure_labels(labels)
        num = gh.create_issue(
            milestone_title=sub["milestone_title"],
            title=sub["title"],
            body=sub["body"],
            labels=labels,
        )
        created.append(num)
        print(f"[orchestrator] Created sub-issue #{num}: {sub['title']}")

    sub_refs = ", ".join(f"#{n}" for n in created)
    gh.close_issue(issue_number, comment=f"Split into sub-issues: {sub_refs}")
    print(f"[orchestrator] Closed #{issue_number} → {sub_refs}")
    return created


def process_issue(issue_number, milestone_title, _depth=0):
    """Run the coder → test → reviewer loop for a single issue."""
    if _depth > 1:
        print(f"[orchestrator] Issue #{issue_number} is a sub-issue of a sub-issue — skipping auto-split.", file=sys.stderr)
        return

    if gh.is_issue_done(issue_number):
        print(f"[orchestrator] Issue #{issue_number} already closed, skipping.")
        return

    feedback    = None
    pr_number   = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[orchestrator] Issue #{issue_number} — attempt {attempt}/{MAX_ATTEMPTS}")

        if pr_number is None:
            pr_number = coder.run_issue(issue_number, feedback=feedback)

        if pr_number is None:
            # Coder timed out — split and recurse (once only)
            sub_issues = split_issue(issue_number)
            for sub in sub_issues:
                process_issue(sub, milestone_title, _depth=_depth + 1)
            return

        # Run tests
        passed, test_output = run_tests()
        if not passed:
            if attempt < MAX_ATTEMPTS:
                print(f"[orchestrator] Test failure on attempt {attempt} — retrying with feedback.")
                feedback  = test_output[-2000:]
                pr_number = None
                continue
            else:
                print(
                    f"[orchestrator] Tests still failing after {MAX_ATTEMPTS} attempts for "
                    f"#{issue_number}. Manual fix required.",
                    file=sys.stderr,
                )
                return

        # Reviewer
        verdict, comment = reviewer.review_pr(pr_number)

        if verdict == "LGTM":
            print(f"[orchestrator] Issue #{issue_number} done. ✓")
            return

        # Reviewer rejected — orchestrator owns the label transition
        gh.update_label(issue_number, add=["revision-needed"], remove=["review-needed"])

        if attempt < MAX_ATTEMPTS:
            print(f"[orchestrator] Changes requested on attempt {attempt} — retrying.")
            feedback  = comment
            pr_number = None
        else:
            print(
                f"[orchestrator] Reviewer still unsatisfied after {MAX_ATTEMPTS} attempts for "
                f"#{issue_number}. Manual fix required.",
                file=sys.stderr,
            )


def run_milestone(milestone_title):
    """Drive the full pipeline for all open issues in a milestone."""
    print(f"[orchestrator] Starting milestone: {milestone_title}")

    seen = set()
    issues = []
    for label in ("agent-todo", "revision-needed", "agent-in-progress"):
        for i in gh.get_issues(milestone_title, label=label):
            if i["number"] not in seen:
                seen.add(i["number"])
                issues.append(i)
    issues.sort(key=lambda x: x["number"])

    if not issues:
        print(f"[orchestrator] No open issues found for milestone '{milestone_title}'.")
        return

    print(f"[orchestrator] {len(issues)} issue(s) to process.")

    for issue in issues:
        process_issue(issue["number"], milestone_title)

    print("\n[orchestrator] Milestone run complete.")
