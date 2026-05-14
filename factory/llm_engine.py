import json
import subprocess
import sys
import threading
import time
from .config import CLAUDE_BIN

DEFAULT_TOOLS = "Write,Read,Edit,Glob,Grep,LS,Bash"
READ_ONLY_TOOLS = "Read,Glob,LS"


def _build_cmd(prompt, system=None, schema=None, tools=DEFAULT_TOOLS, stream=False):
    cmd = [CLAUDE_BIN, "-p", prompt, "--dangerously-skip-permissions"]

    if tools:
        cmd += ["--allowedTools", tools]

    if system:
        cmd += ["--system-prompt", system]

    if schema:
        cmd += ["--output-format", "json", "--json-schema", json.dumps(schema)]
    elif not stream:
        cmd += ["--output-format", "json"]

    return cmd


def _parse_result(raw, schema=None):
    """Extract the text content from a --output-format json response."""
    try:
        wrapper = json.loads(raw)
        # claude --output-format json wraps the response in {"result": "..."}
        text = wrapper.get("result") or wrapper.get("content") or raw
    except (json.JSONDecodeError, AttributeError):
        text = raw

    if schema is None:
        return text

    # Try to parse the content itself as JSON
    if isinstance(text, (dict, list)):
        return text

    text_str = str(text).strip()

    # Strip markdown fences if present
    if text_str.startswith("```"):
        lines = text_str.splitlines()
        text_str = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    # Find first JSON structure if there's leading prose
    for start_char in ("[", "{"):
        idx = text_str.find(start_char)
        if idx != -1:
            text_str = text_str[idx:]
            break

    return json.loads(text_str)


def run_claude(prompt, system=None, schema=None, tools=DEFAULT_TOOLS, timeout=120):
    """
    Synchronous Claude call. Returns (success: bool, result: str | dict | list).

    Uses --output-format json for structured capture. If schema is provided the
    result is parsed and validated as JSON; otherwise returns the raw text string.
    """
    cmd = _build_cmd(prompt, system=system, schema=schema, tools=tools)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"[llm] timed out after {timeout}s", file=sys.stderr)
        return False, None

    if result.returncode != 0:
        print(f"[llm] claude exited {result.returncode}: {result.stderr.strip()}", file=sys.stderr)
        return False, None

    if schema is not None:
        try:
            parsed = _parse_result(result.stdout, schema=schema)
            return True, parsed
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[llm] JSON parse error: {e}", file=sys.stderr)
            print(f"[llm] raw output: {result.stdout[:500]}", file=sys.stderr)
            return False, None

    text = _parse_result(result.stdout)
    return True, text


def run_claude_stream(prompt, system=None, tools=DEFAULT_TOOLS, timeout=600):
    """
    Streaming Claude call for long-running coder operations.

    Pipes stdout line-by-line with a [coder] prefix. A heartbeat thread prints
    elapsed time every 30 s. Returns (success: bool).
    """
    cmd = _build_cmd(prompt, system=system, tools=tools, stream=True)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,  # stream directly — avoids pipe buffer deadlock
            text=True,
            bufsize=1,
        )
    except OSError as e:
        print(f"[llm] failed to start claude: {e}", file=sys.stderr)
        return False

    start = time.time()
    last_activity = [start]
    done = threading.Event()

    def reader():
        for line in proc.stdout:
            print(f"[coder] {line}", end="")
            last_activity[0] = time.time()
        done.set()

    def heartbeat():
        while not done.wait(timeout=30):
            elapsed = int(time.time() - start)
            idle = int(time.time() - last_activity[0])
            print(f"[coder] {elapsed}s elapsed — last activity {idle}s ago", file=sys.stderr)

    t_reader = threading.Thread(target=reader, daemon=True)
    t_beat   = threading.Thread(target=heartbeat, daemon=True)
    t_reader.start()
    t_beat.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"[llm] coder timed out after {timeout}s", file=sys.stderr)
        return False
    finally:
        done.set()

    t_reader.join(timeout=5)

    if proc.returncode != 0:
        print(f"[llm] claude exited {proc.returncode}", file=sys.stderr)
        return False

    return True
