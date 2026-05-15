import json
import subprocess
import sys
from .config import GH_BIN, GITHUB_REPO

LABEL_COLORS = {
    "agent-todo":        "0075ca",
    "agent-in-progress": "e4e669",
    "review-needed":     "d93f0b",
    "revision-needed":   "b60205",
    "agent-done":        "0e8a16",
}


def _run(args, check=True):
    result = subprocess.run([GH_BIN] + args, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        result.check_returncode()
    return result


def merge_labels(labels, *extra):
    """Return a deduplicated list containing labels plus any extra labels."""
    return list(set(list(labels) + list(extra)))


def ensure_labels(labels):
    for label in labels:
        color = LABEL_COLORS.get(label, "cccccc")
        _run(["label", "create", label,
              "--repo", GITHUB_REPO, "--color", color, "--force"], check=False)


def create_milestone(title, description=""):
    result = _run([
        "api", f"repos/{GITHUB_REPO}/milestones",
        "--method", "POST",
        "--raw-field", f"title={title}",
        "--raw-field", f"description={description}",
    ], check=False)
    if result.returncode != 0:
        existing = _run(["api", f"repos/{GITHUB_REPO}/milestones", "--paginate"])
        for m in json.loads(existing.stdout):
            if m["title"] == title:
                return m["number"]
        return None
    return json.loads(result.stdout)["number"]


def create_issue(milestone_title, title, body, labels):
    ensure_labels(labels)

    args = ["issue", "create", "--repo", GITHUB_REPO, "--title", title, "--body", body]
    for label in labels:
        args += ["--label", label]
    if milestone_title:
        args += ["--milestone", milestone_title]

    url = _run(args).stdout.strip()
    try:
        return int(url.rstrip("/").split("/")[-1])
    except (ValueError, IndexError):
        raise RuntimeError(f"gh returned unexpected output when creating issue (expected URL, got: {url!r})")


def get_issues(milestone_title, label=None):
    args = ["issue", "list", "--repo", GITHUB_REPO,
            "--state", "open", "--limit", "200",
            "--json", "number,title,body,labels,state"]
    if label:
        args += ["--label", label]
    if milestone_title:
        args += ["--milestone", milestone_title]
    return sorted(json.loads(_run(args).stdout), key=lambda x: x["number"])


def get_issue(number):
    return json.loads(_run([
        "issue", "view", str(number), "--repo", GITHUB_REPO,
        "--json", "number,title,body,labels,state",
    ]).stdout)


def update_label(issue_number, add=None, remove=None):
    for label in (remove or []):
        _run(["issue", "edit", str(issue_number),
              "--repo", GITHUB_REPO, "--remove-label", label], check=False)
    for label in (add or []):
        ensure_labels([label])
        _run(["issue", "edit", str(issue_number),
              "--repo", GITHUB_REPO, "--add-label", label], check=False)


def find_open_pr_for_issue(issue_number):
    result = _run(["pr", "list", "--repo", GITHUB_REPO,
                   "--state", "open", "--json", "number,body"], check=False)
    if result.returncode != 0:
        return None
    needle = f"Closes #{issue_number}"
    for pr in json.loads(result.stdout):
        if needle in (pr.get("body") or ""):
            return pr["number"]
    return None


def is_issue_done(issue_number):
    return get_issue(issue_number).get("state", "").upper() == "CLOSED"


def create_pr(title, body, head, base="main"):
    ensure_labels(["review-needed"])
    url = _run([
        "pr", "create", "--repo", GITHUB_REPO,
        "--title", title, "--body", body,
        "--head", head, "--base", base, "--label", "review-needed",
    ]).stdout.strip()
    try:
        return int(url.rstrip("/").split("/")[-1])
    except (ValueError, IndexError):
        raise RuntimeError(f"gh returned unexpected output when creating PR (expected URL, got: {url!r})")


def get_pr(pr_number):
    return json.loads(_run([
        "pr", "view", str(pr_number), "--repo", GITHUB_REPO,
        "--json", "number,title,body,state,headRefName",
    ]).stdout)


def get_diff(pr_number):
    result = _run(["pr", "diff", str(pr_number), "--repo", GITHUB_REPO], check=False)
    if result.returncode != 0:
        print(f"[reviewer] Could not fetch diff for PR #{pr_number}: {result.stderr.strip()}", file=sys.stderr)
        return None
    return result.stdout


def post_comment(pr_number, body):
    _run(["pr", "comment", str(pr_number), "--repo", GITHUB_REPO, "--body", body])


def merge_pr(pr_number):
    result = _run(["pr", "merge", str(pr_number), "--repo", GITHUB_REPO, "--squash", "--delete-branch"], check=False)
    if result.returncode != 0:
        print(f"[reviewer] gh pr merge failed: {result.stderr.strip()}", file=sys.stderr)
    return result.returncode == 0


def close_issue(issue_number, comment=""):
    if comment:
        _run(["issue", "comment", str(issue_number), "--repo", GITHUB_REPO, "--body", comment])
    _run(["issue", "close", str(issue_number), "--repo", GITHUB_REPO])
