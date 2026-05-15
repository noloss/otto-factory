# otto-factory project instructions

## Test-first workflow

Before making any change to `factory/`:

1. Write tests for the expected new behaviour in `tests/`
2. Make the code changes
3. Run `pytest tests/ -v` — all tests must pass before the task is done
4. Keep tests up-to-date: if behaviour changes, update the relevant tests (don't delete them)

Run the suite with: `source venv/bin/activate && pytest tests/ -v`

## Debugging rules

When an error is reported, always follow this sequence — no exceptions:

1. **Read the relevant code first.** Trace the failure path from the error back to the source. Do not guess based on the error message alone.
2. **State the root cause hypothesis** before proposing any fix. Explain which file and line is the source, and why.
3. **If the root cause requires runtime information** (environment variables, PATH, exit codes, file contents, shell behaviour), ask the user to run a specific diagnostic command and wait for the output before writing any code.
4. **Only then write the fix** — targeted to the confirmed root cause, not the symptom.

If steps 1–3 show the cause is unambiguous, you may proceed directly to the fix while explaining your reasoning. But if there is any uncertainty about the runtime environment, always ask first.

## Before rewriting any module

If a working older version exists (e.g. in `framework/`), read it first. Understand why it works before writing a replacement. Don't invent patterns that the old code already solved correctly.

## When changing a function signature

Search all callers before changing any function signature, return type, or parameter. List the files that will break and fix them in the same change.

## Environment assumptions

Never assume a CLI flag, shell alias, or environment variable exists without verifying it. For shell tooling (nvm, pyenv, gh, claude), check what is actually available before writing commands that depend on it. When in doubt, ask the user to run `which <tool>` or equivalent.

## Scope discipline

The coder agent runs in `TARGET_DIR`. Any prompt, config, or code change that touches file paths must confirm it stays within `TARGET_DIR`. Claude CLI with `--dangerously-skip-permissions` will write anywhere — the prompt must be explicit about boundaries.

## When tests keep failing

If a test fails more than once with the same root error after a fix, stop and re-diagnose from scratch rather than retrying variations of the same fix. A repeated failure means the hypothesis was wrong.
