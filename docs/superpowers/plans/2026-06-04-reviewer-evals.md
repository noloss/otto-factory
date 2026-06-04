# Reviewer Evals with LangSmith — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a LangSmith-tracked eval suite for the reviewer agent that validates prompt quality against a fixed set of `.diff` fixtures.

**Architecture:** A `@traceable` decorator on `run_claude()` sends traces to LangSmith on every real Claude call. Eval tests in `tests/evals/` mock only GitHub write operations and load fixture diffs from local files; real Claude runs. Tests are marked `@pytest.mark.llm` so the fast suite is unaffected.

**Tech Stack:** `langsmith` Python SDK, `pytest`, `unittest.mock`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `requirements.txt` | Modify | Add `langsmith>=0.1` |
| `pyproject.toml` | Modify | Register `llm` pytest marker |
| `factory/llm_engine.py` | Modify | Add `@traceable` to `run_claude()` |
| `.env` | Modify | Add three LangSmith env vars |
| `tests/evals/__init__.py` | Create | Make evals a package |
| `tests/evals/fixtures/hardcoded_aws_key.diff` | Create | Fixture: credential leak |
| `tests/evals/fixtures/readme_typo.diff` | Create | Fixture: clean text change |
| `tests/evals/fixtures/sql_string_concat.diff` | Create | Fixture: SQL injection |
| `tests/evals/fixtures/clean_refactor.diff` | Create | Fixture: safe refactor with tests |
| `tests/evals/reviewer_cases.py` | Create | CASES list: fixture → expected verdict |
| `tests/evals/test_reviewer.py` | Create | Parametrized eval tests |

---

## Task 1: Install langsmith and register the pytest marker

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add langsmith to requirements.txt**

Open `requirements.txt`. It currently contains:
```
python-dotenv>=1.0.0
jsonschema>=4.0.0
pytest>=8.0.0
```

Add one line:
```
python-dotenv>=1.0.0
jsonschema>=4.0.0
pytest>=8.0.0
langsmith>=0.1
```

- [ ] **Step 2: Install into the venv**

```bash
source venv/bin/activate && pip install langsmith
```

Expected: `Successfully installed langsmith-...` (version may vary)

- [ ] **Step 3: Register the llm marker in pyproject.toml**

`pyproject.toml` currently contains:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Replace with:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-m 'not llm'"
markers = [
    "llm: marks tests that make real LLM calls (run explicitly with '-m llm')",
]
```

- [ ] **Step 4: Verify existing tests still pass**

```bash
source venv/bin/activate && pytest tests/ -v
```

Expected: all existing tests pass, no warnings about unknown markers.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "chore: add langsmith dependency and llm pytest marker"
```

---

## Task 2: Add @traceable to run_claude()

**Files:**
- Modify: `factory/llm_engine.py`

The `@traceable` decorator from LangSmith is a no-op when `LANGCHAIN_TRACING_V2` is not set to `"true"`. It does not change function behaviour, inputs, outputs, or exception handling — it only sends a trace to LangSmith when tracing is active.

- [ ] **Step 1: Write a test that will confirm the decorator doesn't break run_claude**

The existing tests in `tests/test_llm_engine.py` already cover `run_claude` via `_parse_result`. We verify the decorator is transparent by running them after the change. No new test needed — but confirm the existing test file covers this path before proceeding:

```bash
source venv/bin/activate && pytest tests/test_llm_engine.py -v
```

Expected: all tests pass. Note the test names so you can confirm they still pass after Step 3.

- [ ] **Step 2: Add the import and decorator to factory/llm_engine.py**

At the top of `factory/llm_engine.py`, after the existing imports, add:

```python
from langsmith import traceable
```

Then decorate `run_claude()`:

```python
@traceable(name="run_claude", run_type="llm")
def run_claude(prompt, system=None, schema=None, tools=DEFAULT_TOOLS, timeout=120, label="llm"):
```

The full function signature is unchanged — only the decorator is added above it.

- [ ] **Step 3: Run the existing llm_engine tests to confirm no regressions**

```bash
source venv/bin/activate && pytest tests/test_llm_engine.py -v
```

Expected: same tests pass as in Step 1. If any fail, the decorator is affecting behaviour — investigate before continuing.

- [ ] **Step 4: Add LangSmith env vars to .env**

Open `.env` (the local one, not committed). Add these three lines:

```
LANGCHAIN_API_KEY=<your key from smith.langchain.com>
LANGCHAIN_PROJECT=otto-factory-reviewer-evals
LANGCHAIN_TRACING_V2=true
```

To get the API key: sign up at smith.langchain.com → Settings → API Keys → Create API Key.

Leave `LANGCHAIN_TRACING_V2` unset (or `false`) until you have a key — the decorator is a no-op without it.

- [ ] **Step 5: Commit**

```bash
git add factory/llm_engine.py
git commit -m "feat: add LangSmith tracing to run_claude()"
```

Do not commit `.env` — it contains your API key.

---

## Task 3: Create fixture diff files

**Files:**
- Create: `tests/evals/__init__.py`
- Create: `tests/evals/fixtures/hardcoded_aws_key.diff`
- Create: `tests/evals/fixtures/readme_typo.diff`
- Create: `tests/evals/fixtures/sql_string_concat.diff`
- Create: `tests/evals/fixtures/clean_refactor.diff`

- [ ] **Step 1: Create the package files**

```bash
mkdir -p tests/evals/fixtures
touch tests/evals/__init__.py
```

- [ ] **Step 2: Create hardcoded_aws_key.diff**

Write this content to `tests/evals/fixtures/hardcoded_aws_key.diff`:

```diff
diff --git a/config.py b/config.py
index 1234abc..5678def 100644
--- a/config.py
+++ b/config.py
@@ -1,5 +1,8 @@
 import os
 
+AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
+
 DEBUG = os.getenv("DEBUG", "false")
 DATABASE_URL = os.getenv("DATABASE_URL")
```

- [ ] **Step 3: Create readme_typo.diff**

Write this content to `tests/evals/fixtures/readme_typo.diff`:

```diff
diff --git a/README.md b/README.md
index 1234abc..5678def 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,5 @@
 # otto-factory
 
-A standalone langauge-agnostic software factory.
+A standalone language-agnostic software factory.
 
 ## Setup
```

- [ ] **Step 4: Create sql_string_concat.diff**

Write this content to `tests/evals/fixtures/sql_string_concat.diff`:

```diff
diff --git a/db.py b/db.py
index 1234abc..5678def 100644
--- a/db.py
+++ b/db.py
@@ -1,6 +1,8 @@
 import sqlite3
 
-def get_user(db, user_id):
-    cursor = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
-    return cursor.fetchone()
+def get_user(db, username):
+    query = "SELECT * FROM users WHERE username = '" + username + "'"
+    cursor = db.execute(query)
+    return cursor.fetchone()
```

- [ ] **Step 5: Create clean_refactor.diff**

Write this content to `tests/evals/fixtures/clean_refactor.diff`:

```diff
diff --git a/utils.py b/utils.py
index 1234abc..5678def 100644
--- a/utils.py
+++ b/utils.py
@@ -1,6 +1,4 @@
 def format_findings(findings):
-    result = ""
-    for f in findings:
-        result = result + "- " + f + "\n"
-    return result
+    return "".join(f"- {f}\n" for f in findings)
diff --git a/tests/test_utils.py b/tests/test_utils.py
new file mode 100644
index 0000000..1234abc
--- /dev/null
+++ b/tests/test_utils.py
@@ -0,0 +1,5 @@
+from utils import format_findings
+
+def test_format_findings():
+    assert format_findings(["a", "b"]) == "- a\n- b\n"
```

- [ ] **Step 6: Commit**

```bash
git add tests/evals/
git commit -m "test: add reviewer eval fixture diffs"
```

---

## Task 4: Create reviewer_cases.py

**Files:**
- Create: `tests/evals/reviewer_cases.py`

- [ ] **Step 1: Write reviewer_cases.py**

Create `tests/evals/reviewer_cases.py` with this content:

```python
CASES = [
    {
        "fixture": "hardcoded_aws_key.diff",
        "description": "hardcoded AWS credentials in config",
        "expect_verdict": "CHANGES_REQUESTED",
        "findings_contain": ["secret", "credential", "key", "aws"],
    },
    {
        "fixture": "readme_typo.diff",
        "description": "readme typo fix",
        "expect_verdict": "LGTM",
        "findings_contain": [],
    },
    {
        "fixture": "sql_string_concat.diff",
        "description": "SQL string concatenation vulnerability",
        "expect_verdict": "CHANGES_REQUESTED",
        "findings_contain": ["sql", "injection", "query", "parameteris", "parameteriz"],
    },
    {
        "fixture": "clean_refactor.diff",
        "description": "clean refactor with tests included",
        "expect_verdict": "LGTM",
        "findings_contain": [],
    },
]
```

Note on `findings_contain`: any single keyword match passes the assertion. The list for `sql_string_concat` includes both British and American spellings of "parameterise/parameterize" since the reviewer may use either.

- [ ] **Step 2: Commit**

```bash
git add tests/evals/reviewer_cases.py
git commit -m "test: add reviewer eval cases config"
```

---

## Task 5: Write the eval tests

**Files:**
- Create: `tests/evals/test_reviewer.py`

- [ ] **Step 1: Write test_reviewer.py**

Create `tests/evals/test_reviewer.py` with this content:

```python
from pathlib import Path
from unittest.mock import patch
import pytest

from factory.reviewer import review_pr
from tests.evals.reviewer_cases import CASES

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.llm
@pytest.mark.parametrize("case", CASES, ids=[c["description"] for c in CASES])
def test_reviewer_eval(case):
    diff = (FIXTURES_DIR / case["fixture"]).read_text()

    with (
        patch("factory.reviewer.gh.get_diff", return_value=diff),
        patch("factory.reviewer.gh.post_comment"),
        patch("factory.reviewer.gh.merge_pr", return_value=True),
    ):
        verdict, findings_text = review_pr(pr_number=99)

    assert verdict == case["expect_verdict"], (
        f"[{case['description']}] "
        f"expected {case['expect_verdict']!r}, got {verdict!r}\n"
        f"findings: {findings_text}"
    )

    findings_lower = findings_text.lower()
    for keyword in case["findings_contain"]:
        if keyword in findings_lower:
            return  # any single match is sufficient

    if case["findings_contain"]:
        pytest.fail(
            f"[{case['description']}] "
            f"findings did not contain any of {case['findings_contain']!r}\n"
            f"actual findings: {findings_text}"
        )
```

- [ ] **Step 2: Verify eval tests are excluded from the fast suite**

The `addopts = "-m 'not llm'"` in `pyproject.toml` means `pytest tests/` automatically excludes llm-marked tests. Verify:

```bash
source venv/bin/activate && pytest tests/ -v 2>&1 | tail -5
```

Expected: eval tests do not appear — they are excluded by the default `addopts`. All non-llm tests pass. Output ends with something like `X passed, Y deselected`.

- [ ] **Step 3: Run the eval suite (requires Claude CLI and optionally LangSmith key)**

```bash
source venv/bin/activate && pytest --override-ini="addopts=" -m llm tests/evals/ -v
```

Expected output per case:
```
PASSED tests/evals/test_reviewer.py::test_reviewer_eval[readme typo fix]
PASSED tests/evals/test_reviewer.py::test_reviewer_eval[hardcoded AWS credentials in config]
...
```

If a test fails, check the assertion message — it prints the actual verdict and findings to help diagnose whether the reviewer prompt needs adjustment or the fixture keywords need expanding.

- [ ] **Step 4: Commit**

```bash
git add tests/evals/test_reviewer.py
git commit -m "test: add LangSmith-tracked reviewer eval suite"
```

---

## Adding New Fixtures (reference)

To add a new eval case in future:

1. Capture a diff:
   ```bash
   gh pr diff 42 > tests/evals/fixtures/my_new_case.diff
   ```
   Or write a minimal `.diff` by hand targeting one specific pattern.

2. Add a row to `CASES` in `tests/evals/reviewer_cases.py`:
   ```python
   {
       "fixture": "my_new_case.diff",
       "description": "short description of the pattern",
       "expect_verdict": "CHANGES_REQUESTED",   # or "LGTM"
       "findings_contain": ["keyword1", "keyword2"],
   },
   ```

3. Run evals to confirm it captures the expected behaviour:
   ```bash
   source venv/bin/activate && pytest --override-ini="addopts=" -m llm tests/evals/ -v -k "my_new_case"
   ```
