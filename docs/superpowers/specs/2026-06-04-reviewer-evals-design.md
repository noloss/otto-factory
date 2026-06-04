# Reviewer Evals with LangSmith — Design

**Date:** 2026-06-04  
**Scope:** Reviewer agent only  
**Goal:** Track how changes to `factory/prompts/reviewer.txt` affect output quality over time

---

## Problem

The reviewer agent's behaviour is controlled by a prompt in `factory/prompts/reviewer.txt`. There is currently no way to know whether a prompt change improves or regresses reviewer quality across a representative set of inputs. Evals give us a before/after comparison on every prompt change.

---

## Architecture

Three parts, all cleanly separated from production factory code:

1. **LangSmith instrumentation** — `@traceable` on `run_claude()` in `factory/llm_engine.py`. LangSmith's decorator is a no-op when `LANGCHAIN_TRACING_V2` is not set to `"true"`, so CI and dev without an account are unaffected. The env var is set alongside `LANGCHAIN_API_KEY` in `.env`.

2. **Fixture files** — raw diff text in `tests/evals/fixtures/*.diff`, committed to the repo. Each file targets one specific pattern (one security issue, one clean change, etc.).

3. **Eval test suite** — `tests/evals/reviewer_cases.py` (case config) and `tests/evals/test_reviewer.py` (parametrized tests). All tests marked `@pytest.mark.llm` so they are excluded from the fast suite.

---

## File Structure

```
tests/evals/
    fixtures/
        hardcoded_aws_key.diff
        readme_typo.diff
        sql_string_concat.diff
        clean_refactor.diff
    reviewer_cases.py
    test_reviewer.py

factory/
    llm_engine.py          ← @traceable added to run_claude()
    prompts/
        reviewer.txt       ← what we are evaluating

docs/superpowers/specs/
    2026-06-04-reviewer-evals-design.md
```

---

## Case Configuration (`reviewer_cases.py`)

```python
CASES = [
    {
        "fixture": "hardcoded_aws_key.diff",
        "description": "hardcoded AWS key in config",
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
        "description": "SQL string concatenation",
        "expect_verdict": "CHANGES_REQUESTED",
        "findings_contain": ["sql", "injection", "query"],
    },
    {
        "fixture": "clean_refactor.diff",
        "description": "clean refactor with tests",
        "expect_verdict": "LGTM",
        "findings_contain": [],
    },
]
```

`findings_contain` is a list of keywords where **any one match** passes the assertion. Matching is case-insensitive. An empty list means no findings check is performed (LGTM cases).

---

## Test Execution (`test_reviewer.py`)

For each case:
1. Load fixture diff from `tests/evals/fixtures/<fixture>`
2. Mock `gh.get_diff` → return fixture content
3. Mock `gh.post_comment` and `gh.merge_pr` → no-ops (no GitHub writes)
4. Call real `review_pr()` → real `run_claude()` → real Claude CLI subprocess
5. `@traceable` sends input prompt + output JSON to LangSmith
6. Assert verdict equals `expect_verdict`
7. Assert findings text contains at least one keyword from `findings_contain`

---

## Running Evals

```bash
# Eval suite only (real Claude calls, sends to LangSmith)
source venv/bin/activate && pytest -m llm tests/evals/ -v

# Fast suite (unaffected — skips llm-marked tests)
source venv/bin/activate && pytest tests/
```

---

## LangSmith Setup

Three env vars added to `.env`:
```
LANGCHAIN_API_KEY=<from langsmith.com>
LANGCHAIN_PROJECT=otto-factory-reviewer-evals
LANGCHAIN_TRACING_V2=true
```

Account creation: [smith.langchain.com](https://smith.langchain.com) — free tier is sufficient.

Each eval suite run creates a group of traces under the project. When `reviewer.txt` is edited, run evals before and after — LangSmith shows pass rate per case across runs side by side.

---

## Fixture Maintenance

- **Adding a case:** `gh pr diff <n> > tests/evals/fixtures/<name>.diff`, then add a row to `CASES`
- **Improving a fixture:** edit the `.diff` file directly — trim to the essential signal, remove noise
- **Knowing what to improve:** flaky cases in LangSmith (flipping pass/fail across runs) indicate ambiguous fixtures or wrong expected verdicts

Keep each fixture focused on **one pattern**. Whole real-world diffs mix multiple signals and make failures hard to interpret.

---

## Assertions

- **Verdict** (`LGTM` / `CHANGES_REQUESTED`): strict equality — this is binary and must be correct
- **Findings keywords**: fuzzy match — LLMs rephrase, so checking intent not exact wording
- `ERROR` verdicts (Claude timeout, auth failure) are not caught by assertions — they surface as unexpected verdict mismatches

---

## Out of Scope

- Planner and coder evals (future work)
- LangSmith `run_on_dataset()` runner (not needed — pytest is sufficient)
- Nested spans / per-agent tracing (can be added later if latency breakdown is needed)
