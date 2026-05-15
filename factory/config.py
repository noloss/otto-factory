import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def _parse_github_repo(value):
    """Accept owner/repo in any of these forms and normalise to 'owner/repo':
      noloss/my-repo
      /noloss/my-repo
      https://github.com/noloss/my-repo
      https://github.com/noloss/my-repo/
    """
    v = (value or "").strip().rstrip("/")
    if v.startswith("https://github.com/"):
        v = v[len("https://github.com/"):]
    elif v.startswith("http://github.com/"):
        v = v[len("http://github.com/"):]
    return v.lstrip("/")


GITHUB_REPO   = os.getenv("GITHUB_REPO", "")
TARGET_DIR    = Path(os.getenv("TARGET_DIR", ".")).resolve()
TEST_COMMAND  = os.getenv("TEST_COMMAND", "")
SOURCE_GLOB   = os.getenv("SOURCE_GLOB", "src")
GH_BIN        = os.getenv("GH_BIN", "gh")
CLAUDE_BIN    = os.getenv("CLAUDE_BIN", "claude")
try:
    CODER_TIMEOUT = int(os.getenv("CODER_TIMEOUT", "600"))
    MAX_ATTEMPTS  = int(os.getenv("MAX_ATTEMPTS", "3"))
except ValueError as e:
    print(f"Error: invalid integer in .env — {e}", file=sys.stderr)
    sys.exit(1)
SHELL_INIT    = os.getenv("SHELL_INIT", "")
PROMPTS_DIR   = Path(__file__).parent / "prompts"

GITHUB_REPO = _parse_github_repo(GITHUB_REPO)

if not GITHUB_REPO:
    print("Error: GITHUB_REPO is not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
    sys.exit(1)

if GITHUB_REPO.count("/") != 1:
    print(f"Error: GITHUB_REPO must be in 'owner/repo' format, got: '{GITHUB_REPO}'", file=sys.stderr)
    print("Accepted formats: 'owner/repo', '/owner/repo', 'https://github.com/owner/repo'", file=sys.stderr)
    sys.exit(1)
