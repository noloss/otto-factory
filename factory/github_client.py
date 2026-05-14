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
    cmd = [GH_BIN, "-R", GITHUB_REPO] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        result.check_returncode()
    return result


def ensure_labels(labels):
    for label in labels:
        color = LABEL_COLORS.get(label, "cccccc")
        _run(["label", "create", label, "--color", color, "--force"], check=False)


def create_milestone(title, description=""):
    result = _run([
        "api", f"repos/{GITHUB_REPO}/milestones",
        "--method", "POST",
        "--raw-field", f"title={title}",
        "--raw-field", f"description={description}",
    ], check=False)
    if result.returncode != 0:
        # may already exist — fetch its number
        existing = _run(["api", f"repos/{GITHUB_REPO}/milestones", "--paginate"])
        milestones = json.loads(existing.stdout)
        for m in milestones:
            if m["title"] == title:
                return m["number"]
        return None
    data = json.loads(result.stdout)
    return data["number"]


def create_issue(milestone_title, title, body, labels):
    ensure_labels(labels)
    milestone_number = _get_milestone_number(milestone_title)

    args = [
        "issue", "create",
        "--title", title,
        "--body", body,
    ]
    for label in labels:
        args += ["--label", label]
    if milestone_number:
        args += ["--milestone", str(milestone_number)]

    result = _run(args)
    # output is a URL like https://github.com/owner/repo/issues/42
    url = result.stdout.strip()
    return int(url.rstrip("/").split("/")[-1])


def _get_milestone_number(title):
    result = _run(["api", f"repos/{GITHUB_REPO}/milestones", "--paginate"], check=False)
    if result.returncode != 0:
        return None
    for m in json.loads(result.stdout):
        if m["title"] == title:
            return m["number"]
    return None


def get_issues(milestone_title, label=None):
    args = ["issue", "list", "--state", "open", "--json", "number,title,body,labels,state"]
    if label:
        args += ["--label", label]
    if milestone_title:
        args += ["--milestone", milestone_title]
    result = _run(args)
    issues = json.loads(result.stdout)
    return sorted(issues, key=lambda x: x["number"])


def get_issue(number):
    result = _run(["issue", "view", str(number), "--json", "number,title,body,labels,state"])
    return json.loads(result.stdout)


def update_label(issue_number, add=None, remove=None):
    for label in (remove or []):
        _run(["issue", "edit", str(issue_number), "--remove-label", label], check=False)
    for label in (add or []):
        ensure_labels([label])
        _run(["issue", "edit", str(issue_number), "--add-label", label], check=False)


def find_open_pr_for_issue(issue_number):
    result = _run(["pr", "list", "--state", "open", "--json", "number,body"], check=False)
    if result.returncode != 0:
        return None
    prs = json.loads(result.stdout)
    needle = f"Closes #{issue_number}"
    for pr in prs:
        if needle in (pr.get("body") or ""):
            return pr["number"]
    return None


def is_issue_done(issue_number):
    issue = get_issue(issue_number)
    return issue.get("state", "").upper() == "CLOSED"


def create_pr(title, body, base="main"):
    ensure_labels(["review-needed"])
    result = _run([
        "pr", "create",
        "--title", title,
        "--body", body,
        "--base", base,
        "--label", "review-needed",
    ])
    url = result.stdout.strip()
    return int(url.rstrip("/").split("/")[-1])


def get_diff(pr_number):
    result = _run(["pr", "diff", str(pr_number)])
    return result.stdout


def post_comment(pr_number, body):
    _run(["pr", "comment", str(pr_number), "--body", body])


def merge_pr(pr_number):
    _run(["pr", "merge", str(pr_number), "--squash", "--delete-branch", "--auto"])


def close_issue(issue_number, comment=""):
    if comment:
        _run(["issue", "comment", str(issue_number), "--body", comment])
    _run(["issue", "close", str(issue_number)])
