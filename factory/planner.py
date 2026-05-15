import sys
from pathlib import Path
from . import github_client as gh
from .github_client import merge_labels
from .llm_engine import run_claude
from .config import PROMPTS_DIR, TEST_COMMAND

PLANNER_SCHEMA = {
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


def plan(prd_path):
    prd_text = Path(prd_path).read_text()
    system   = (PROMPTS_DIR / "planner.txt").read_text()

    test_hint = (
        f"Each release must include a final acceptance criterion: the test suite runs with "
        f"`{TEST_COMMAND}` and exits 0."
        if TEST_COMMAND else ""
    )

    prompt = f"{prd_text}\n\n{test_hint}".strip()

    print("[planner] Calling Claude to analyse PRD…")
    ok, issues = run_claude(prompt, system=system, schema=PLANNER_SCHEMA, timeout=180, label="planner")

    if not ok or not issues:
        print("[planner] Failed to get a valid plan from Claude.", file=sys.stderr)
        sys.exit(1)

    milestones_created = {}

    for issue in issues:
        ms_title = issue["milestone_title"]
        ms_desc  = issue["milestone_desc"]

        if ms_title not in milestones_created:
            ms_num = gh.create_milestone(ms_title, ms_desc)
            milestones_created[ms_title] = ms_num
            print(f"[planner] Milestone: {ms_title} (#{ms_num})")

        labels = merge_labels(issue.get("labels", []), "agent-todo")
        gh.ensure_labels(labels)

        issue_num = gh.create_issue(
            milestone_title=ms_title,
            title=issue["title"],
            body=issue["body"],
            labels=labels,
        )
        print(f"[planner] Created issue #{issue_num}: {issue['title']}")

    print(f"[planner] Done — {len(issues)} issue(s) created.")
