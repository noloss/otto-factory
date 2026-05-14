import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

GITHUB_REPO   = os.getenv("GITHUB_REPO", "")
TARGET_DIR    = Path(os.getenv("TARGET_DIR", ".")).resolve()
TEST_COMMAND  = os.getenv("TEST_COMMAND", "")
SOURCE_GLOB   = os.getenv("SOURCE_GLOB", "src")
GH_BIN        = os.getenv("GH_BIN", "gh")
CLAUDE_BIN    = os.getenv("CLAUDE_BIN", "claude")
CODER_TIMEOUT = int(os.getenv("CODER_TIMEOUT", "600"))
MAX_ATTEMPTS  = int(os.getenv("MAX_ATTEMPTS", "3"))
PROMPTS_DIR   = Path(__file__).parent / "prompts"
