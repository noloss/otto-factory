import re
import subprocess
import sys
from . import github_client as gh
from .llm_engine import run_claude_stream, DEFAULT_TOOLS
from .config import TARGET_DIR, SOURCE_GLOB, CODER_TIMEOUT, PROMPTS_DIR


def _git(args, check=True):
    result = subprocess.run(
        ["git"] + args,
        cwd=TARGET_DIR,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        print(f"[coder] git error: {result.stderr.strip()}", file=sys.stderr)
        result.check_returncode()
    return result


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]


def _branch_exists_locally(branch):
    r = _git(["branch", "--list", branch], check=False)
    return branch in r.stdout



def run_issue(issue_number, feedback=None):
    """
    Implement a GitHub issue on a feature branch and open a PR.
    Returns the PR number on success, or None on timeout/failure.
    """
    issue  = gh.get_issue(issue_number)
    title  = issue["title"]
    branch = f"feature/issue-{issue_number}-{_slug(title)}"

    # Update label state
    gh.update_label(issue_number, add=["agent-in-progress"], remove=["agent-todo", "revision-needed"])

    existing_pr = gh.find_open_pr_for_issue(issue_number)

    if feedback and existing_pr:
        # Retry on existing branch with reviewer/test feedback
        print(f"[coder] Retrying #{issue_number} on branch {branch}")
        _git(["checkout", branch])
    elif _branch_exists_locally(branch) and not existing_pr:
        # Interrupted run — reset to origin/main for a clean start
        print(f"[coder] Resetting interrupted branch {branch}")
        _git(["checkout", branch])
        _git(["fetch", "origin"])
        _git(["reset", "--hard", "origin/main"])
    else:
        # Fresh start
        print(f"[coder] Starting fresh on #{issue_number}")
        _git(["checkout", "main"])
        _git(["pull", "origin", "main"])
        _git(["checkout", "-b", branch])

    system = (PROMPTS_DIR / "coder.txt").read_text()

    task = f"Issue title: {title}\n\nIssue body:\n{issue['body']}"
    if feedback:
        task += f"\n\n---\nPrevious attempt feedback (fix these issues):\n{feedback}"

    print(f"[coder] Running Claude on issue #{issue_number}…")
    success = run_claude_stream(task, system=system, tools=DEFAULT_TOOLS, timeout=CODER_TIMEOUT)

    if not success:
        print(f"[coder] Claude failed or timed out for #{issue_number}", file=sys.stderr)
        gh.update_label(issue_number, add=["agent-todo"], remove=["agent-in-progress"])
        return None

    # Stage source files and commit
    _git(["add", SOURCE_GLOB], check=False)

    diff_check = _git(["diff", "--cached", "--stat"], check=False)
    if not diff_check.stdout.strip():
        print(f"[coder] No changes staged for #{issue_number}", file=sys.stderr)
        gh.update_label(issue_number, add=["agent-todo"], remove=["agent-in-progress"])
        return None

    if feedback:
        commit_msg = f"fix: address review feedback (#{issue_number})"
    else:
        commit_msg = f"feat: {title} (closes #{issue_number})"

    _git(["commit", "-m", commit_msg])

    if existing_pr:
        _git(["push", "origin", branch])
        print(f"[coder] Pushed to existing PR #{existing_pr}")
        gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
        return existing_pr
    else:
        _git(["push", "-u", "origin", branch])
        pr_number = gh.create_pr(
            title=f"{title}",
            body=f"Closes #{issue_number}\n\n{issue['body'][:500]}",
        )
        print(f"[coder] Opened PR #{pr_number} for issue #{issue_number}")
        gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
        return pr_number
