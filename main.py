#!/usr/bin/env python3
"""
otto-factory — Agentic Orchestrator
Usage:
  python main.py plan   --prd <path>
  python main.py run    --milestone <title>
  python main.py code   --issue <number>
  python main.py review --pr <number>
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Load .env early so CLAUDE_BIN / GH_BIN overrides are visible before preflight
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not installed yet — checked below


def _preflight():
    """Check that required tools are installed and authenticated before running."""

    # --- dotenv available? ------------------------------------------------
    try:
        import dotenv  # noqa: F401
    except ImportError:
        print("Error: python-dotenv is not installed.")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    # --- claude on PATH? --------------------------------------------------
    claude_bin = os.getenv("CLAUDE_BIN", "claude")
    if not shutil.which(claude_bin):
        print(f"Error: '{claude_bin}' is not on your PATH.")
        print("Install Claude Code and make sure 'claude' is available in your terminal.")
        print("See: https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(1)

    # --- gh installed? ----------------------------------------------------
    gh_bin = os.getenv("GH_BIN", "gh")
    if not shutil.which(gh_bin):
        print(f"Error: '{gh_bin}' is not on your PATH.")
        print("Install the GitHub CLI: https://cli.github.com")
        sys.exit(1)

    # --- gh authenticated? ------------------------------------------------
    auth_check = subprocess.run(
        [gh_bin, "auth", "status"],
        capture_output=True,
    )
    if auth_check.returncode != 0:
        print("GitHub CLI is not authenticated.")
        try:
            answer = input("Run 'gh auth login' now? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(1)

        if answer in ("", "y", "yes"):
            login = subprocess.run([gh_bin, "auth", "login"])
            if login.returncode != 0:
                print("Authentication failed. Please run 'gh auth login' manually.", file=sys.stderr)
                sys.exit(1)
            # Confirm it worked
            recheck = subprocess.run([gh_bin, "auth", "status"], capture_output=True)
            if recheck.returncode != 0:
                print("Still not authenticated after login. Please try 'gh auth login' manually.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Cannot continue without GitHub authentication.", file=sys.stderr)
            sys.exit(1)


def cmd_plan(args):
    from factory.planner import plan
    plan(args.prd)


def cmd_run(args):
    from factory.orchestrator import run_milestone
    run_milestone(args.milestone)


def cmd_code(args):
    from factory import coder
    pr = coder.run_issue(args.issue, feedback=args.feedback or None)
    if pr:
        print(f"PR #{pr} opened.")
    else:
        print("Coder failed or timed out.", file=sys.stderr)
        sys.exit(1)


def cmd_review(args):
    from factory import reviewer
    verdict, comment = reviewer.review_pr(args.pr)
    print(f"Verdict: {verdict}")
    if comment:
        print(comment)
    if verdict == "CHANGES_REQUESTED":
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="otto-factory",
        description="Agentic Orchestrator: plan → code → review, driven by GitHub Issues.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Create GitHub issues from a PRD file")
    p_plan.add_argument("--prd", required=True, help="Path to PRD file")

    p_run = sub.add_parser("run", help="Run the full pipeline for a milestone")
    p_run.add_argument("--milestone", required=True, help="Milestone title (e.g. 'Release 1')")

    p_code = sub.add_parser("code", help="Run the coder agent on a single issue")
    p_code.add_argument("--issue", required=True, type=int, help="GitHub issue number")
    p_code.add_argument("--feedback", default="", help="Optional feedback for retry")

    p_review = sub.add_parser("review", help="Run the reviewer agent on a single PR")
    p_review.add_argument("--pr", required=True, type=int, help="GitHub PR number")

    args = parser.parse_args()
    _preflight()

    dispatch = {
        "plan":   cmd_plan,
        "run":    cmd_run,
        "code":   cmd_code,
        "review": cmd_review,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
