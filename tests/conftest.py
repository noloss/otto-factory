"""Set required env vars before any factory module is imported.

factory.config validates at import time and calls sys.exit() if GITHUB_REPO
is missing. Setting these here ensures the real modules load cleanly in tests.
"""
import os

os.environ.setdefault("GITHUB_REPO", "test-owner/test-repo")
os.environ.setdefault("CODER_TIMEOUT", "60")
os.environ.setdefault("MAX_ATTEMPTS", "3")
os.environ.setdefault("TARGET_DIR", "/tmp/otto-test-target")
