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
import sys


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

    dispatch = {
        "plan":   cmd_plan,
        "run":    cmd_run,
        "code":   cmd_code,
        "review": cmd_review,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
