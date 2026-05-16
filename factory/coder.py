import re
import subprocess
import sys
from . import github_client as gh
from .llm_engine import run_claude_stream, DEFAULT_TOOLS, RateLimitError
from .config import TARGET_DIR, SOURCE_GLOB, CODER_TIMEOUT, PROMPTS_DIR


_PR_BODY_LIMIT = 500
_GIT_TIMEOUT   = 60


def _git(args, check=True):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=TARGET_DIR,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"[coder] git {args[0]} timed out after {_GIT_TIMEOUT}s", file=sys.stderr)
        raise
    if check and result.returncode != 0:
        print(f"[coder] git error: {result.stderr.strip()}", file=sys.stderr)
        result.check_returncode()
    return result


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]


def _parse_count(result):
    """Return the integer from a git rev-list --count result, or 0 on failure."""
    return int(result.stdout.strip() or "0") if result.returncode == 0 else 0


def _branch_exists_locally(branch):
    r = _git(["branch", "--list", branch], check=False)
    return branch in r.stdout.split()


def cleanup_after_merge(issue_number):
    """Sync local main with origin and delete the local feature branch.

    Called after a PR is merged. Failure is logged but never propagates —
    a stale local branch is annoying but must not abort the pipeline.
    """
    try:
        issue  = gh.get_issue(issue_number)
        branch = f"feature/issue-{issue_number}-{_slug(issue['title'])}"
        _git(["checkout", "main"])
        _git(["pull", "origin", "main"])
        r = _git(["branch", "-d", branch], check=False)
        if r.returncode != 0:
            _git(["branch", "-D", branch], check=False)
        print(f"[coder] Cleaned up local branch {branch}.")
    except Exception as exc:
        print(f"[coder] Warning: branch cleanup failed for #{issue_number}: {exc}", file=sys.stderr)


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

    if existing_pr:
        # Resume or retry on the existing branch — pull to sync with remote first
        print(f"[coder] Resuming branch {branch} for existing PR #{existing_pr}")
        _git(["fetch", "origin"])
        _git(["checkout", branch])
        _git(["reset", "--hard", f"origin/{branch}"])
        # Rebase onto latest main to prevent stale-branch merge failures
        rebase = _git(["rebase", "origin/main"], check=False)
        if rebase.returncode == 0:
            ahead = _git(["rev-list", "--count", f"origin/{branch}..HEAD"], check=False)
            if _parse_count(ahead) > 0:
                _git(["push", "--force-with-lease", "origin", branch])
                print(f"[coder] Rebased {branch} onto origin/main and force-pushed.")
            # If the only issue was the merge conflict, skip Claude and let reviewer retry
            if feedback and "rebase" in feedback.lower():
                gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
                return existing_pr
        else:
            _git(["rebase", "--abort"], check=False)
            print(f"[coder] Rebase onto origin/main had conflicts — Claude will resolve.", file=sys.stderr)
            conflict_note = "The branch has merge conflicts with origin/main. Resolve the conflicts before committing."
            feedback = f"{conflict_note}\n\n{feedback}" if feedback else conflict_note
    elif _branch_exists_locally(branch):
        _git(["fetch", "origin"])

        # Check if remote already has the commit (push succeeded but PR creation crashed)
        remote_ahead = _git(["rev-list", "--count", f"origin/main..origin/{branch}"], check=False)
        if _parse_count(remote_ahead) > 0:
            print(f"[coder] Remote branch {branch} already pushed — opening PR directly.")
            pr_number = gh.create_pr(
                title=title,
                body=f"Closes #{issue_number}\n\n{issue['body'][:_PR_BODY_LIMIT]}",
                head=branch,
            )
            print(f"[coder] Opened PR #{pr_number} for issue #{issue_number}")
            gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
            return pr_number

        _git(["checkout", branch])

        # Check for local commits ahead of origin/main not yet pushed
        local_ahead = _git(["rev-list", "--count", "origin/main..HEAD"], check=False)
        if _parse_count(local_ahead) > 0:
            print(f"[coder] Resuming interrupted branch {branch} — local commit found, pushing and opening PR.")
            _git(["push", "-u", "origin", branch])
            pr_number = gh.create_pr(
                title=title,
                body=f"Closes #{issue_number}\n\n{issue['body'][:_PR_BODY_LIMIT]}",
                head=branch,
            )
            print(f"[coder] Opened PR #{pr_number} for issue #{issue_number}")
            gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
            return pr_number

        # Check for uncommitted work that can be staged
        _git(["add", SOURCE_GLOB], check=False)
        diff_check = _git(["diff", "--cached", "--stat"], check=False)
        if diff_check.stdout.strip():
            print(f"[coder] Resuming interrupted branch {branch} — staged changes found, skipping Claude.")
            return _commit_and_push(issue_number, branch, existing_pr=None, feedback=feedback, title=title, issue=issue)

        # Nothing to recover — reset and re-run
        print(f"[coder] Resetting interrupted branch {branch} — no recoverable changes.")
        _git(["reset", "--hard", "origin/main"])
    else:
        # Fresh start
        print(f"[coder] Starting fresh on #{issue_number}")
        _git(["checkout", "main"])
        _git(["pull", "origin", "main"])
        _git(["checkout", "-b", branch])

    system = (PROMPTS_DIR / "coder.txt").read_text()

    task = f"TARGET_DIR: {TARGET_DIR}\n\nIssue title: {title}\n\nIssue body:\n{issue['body']}"
    if feedback:
        task += f"\n\n---\nPrevious attempt feedback (fix these issues):\n{feedback}"

    print(f"[coder] Running Claude on issue #{issue_number}…")
    try:
        success = run_claude_stream(task, system=system, tools=DEFAULT_TOOLS, timeout=CODER_TIMEOUT)
    except RateLimitError:
        gh.update_label(issue_number, add=["agent-todo"], remove=["agent-in-progress"])
        raise

    if not success:
        print(f"[coder] Claude failed or timed out for #{issue_number}", file=sys.stderr)
        gh.update_label(issue_number, add=["agent-todo"], remove=["agent-in-progress"])
        return None

    # Stage source files and commit
    _git(["add", SOURCE_GLOB], check=False)

    diff_check = _git(["diff", "--cached", "--stat"], check=False)
    if not diff_check.stdout.strip():
        print(
            f"[coder] No changes staged for #{issue_number}. "
            f"Claude wrote files outside SOURCE_GLOB='{SOURCE_GLOB}'. "
            f"Set SOURCE_GLOB=. in .env if your project has no src/ folder.",
            file=sys.stderr,
        )
        gh.update_label(issue_number, add=["agent-todo"], remove=["agent-in-progress"])
        return "NO_CHANGES"

    return _commit_and_push(issue_number, branch, existing_pr, feedback, title, issue)


def _commit_and_push(issue_number, branch, existing_pr, feedback, title, issue):
    commit_msg = (
        f"fix: address review feedback (#{issue_number})"
        if feedback else
        f"feat: {title} (closes #{issue_number})"
    )
    _git(["commit", "-m", commit_msg])

    if existing_pr:
        _git(["push", "origin", branch])
        print(f"[coder] Pushed to existing PR #{existing_pr}")
        gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
        return existing_pr
    else:
        _git(["push", "-u", "origin", branch])
        pr_number = gh.create_pr(
            title=title,
            body=f"Closes #{issue_number}\n\n{issue['body'][:_PR_BODY_LIMIT]}",
            head=branch,
        )
        print(f"[coder] Opened PR #{pr_number} for issue #{issue_number}")
        gh.update_label(issue_number, add=["review-needed"], remove=["agent-in-progress"])
        return pr_number
