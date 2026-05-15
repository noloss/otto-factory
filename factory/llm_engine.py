import json
import subprocess
import sys
import threading
import time
from .config import CLAUDE_BIN

DEFAULT_TOOLS = "Write,Read,Edit,Glob,Grep,LS,Bash"
READ_ONLY_TOOLS = "Read,Glob,LS"

_RATE_LIMIT_MARKER = "You've hit your limit"


class RateLimitError(Exception):
    """Raised when the Claude API returns a rate limit (HTTP 429)."""


def _build_cmd(prompt, system=None, schema=None, tools=DEFAULT_TOOLS, stream=False):
    cmd = [CLAUDE_BIN, "-p", prompt, "--dangerously-skip-permissions"]

    if tools:
        cmd += ["--allowedTools", tools]

    if system:
        cmd += ["--system-prompt", system]

    if not stream:
        cmd += ["--output-format", "json"]

    return cmd


def _parse_result(raw, schema=None):
    """Extract the text content from a --output-format json response.

    The claude CLI concatenates multiple JSON objects in stdout without any
    separator. Use raw_decode() to walk through them and find type=result.
    """
    decoder = json.JSONDecoder()
    pos = 0
    wrapper = None
    while pos < len(raw):
        while pos < len(raw) and raw[pos] in " \t\r\n":
            pos += 1
        if pos >= len(raw):
            break
        try:
            obj, pos = decoder.raw_decode(raw, pos)
            if isinstance(obj, dict) and obj.get("type") == "result":
                wrapper = obj
                break
        except json.JSONDecodeError as e:
            print(f"[llm] JSON decode error at pos {pos}: {e} — snippet: {raw[pos:pos+80]!r}", file=sys.stderr)
            break

    text = raw
    if wrapper is not None:
        text = wrapper.get("result") or wrapper.get("content") or raw

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

    # Find whichever JSON structure starts first (object or array)
    positions = {c: text_str.find(c) for c in ("[", "{") if text_str.find(c) != -1}
    if positions:
        idx = min(positions.values())
        obj, _ = json.JSONDecoder().raw_decode(text_str, idx)
        return obj

    return json.loads(text_str)


def run_claude(prompt, system=None, schema=None, tools=DEFAULT_TOOLS, timeout=120, label="llm"):
    """
    Synchronous Claude call. Returns (success: bool, result: str | dict | list).

    Uses --output-format json for structured capture. If schema is provided the
    result is parsed and validated as JSON; otherwise returns the raw text string.
    A heartbeat thread prints elapsed time every 15 s so the terminal stays alive.
    """
    cmd = _build_cmd(prompt, system=system, schema=schema, tools=tools)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as e:
        print(f"[{label}] failed to start claude: {e}", file=sys.stderr)
        return False, None

    _THINKING_WORDS = [
        "Manifesting", "Scheming", "Pondering", "Conjuring", "Plotting",
        "Cogitating", "Deliberating", "Ruminating", "Synthesizing", "Divining",
        "Theorising", "Calculating", "Contemplating", "Orchestrating", "Channeling",
    ]

    start = time.time()
    done = threading.Event()

    def heartbeat():
        i = 0
        while not done.wait(timeout=15):
            word = _THINKING_WORDS[i % len(_THINKING_WORDS)]
            elapsed = int(time.time() - start)
            print(f"[{label}] {word}… ({elapsed}s)", file=sys.stderr)
            i += 1

    t_beat = threading.Thread(target=heartbeat, daemon=True)
    t_beat.start()

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        done.set()
        print(f"[{label}] timed out after {timeout}s", file=sys.stderr)
        return False, None
    finally:
        done.set()

    if proc.returncode != 0:
        print(f"[{label}] claude exited {proc.returncode}", file=sys.stderr)
        if stderr.strip():
            print(f"[{label}] stderr: {stderr.strip()}", file=sys.stderr)
        if stdout.strip():
            print(f"[{label}] stdout: {stdout.strip()[:1000]}", file=sys.stderr)
        # Detect rate limit via the JSON result field
        try:
            obj, _ = json.JSONDecoder().raw_decode(stdout.strip())
            if isinstance(obj, dict) and obj.get("api_error_status") == 429:
                raise RateLimitError(_RATE_LIMIT_MARKER)
        except (json.JSONDecodeError, StopIteration, ValueError):
            pass
        return False, None

    if schema is not None:
        try:
            parsed = _parse_result(stdout, schema=schema)
            return True, parsed
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[{label}] JSON parse error: {e}", file=sys.stderr)
            print(f"[{label}] raw output: {stdout[:500]}", file=sys.stderr)
            return False, None

    text = _parse_result(stdout)
    return True, text


def run_claude_stream(prompt, system=None, tools=DEFAULT_TOOLS, timeout=600, label="coder"):
    """
    Streaming Claude call for long-running operations.

    Pipes stdout line-by-line with a [label] prefix. A heartbeat thread prints
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
        print(f"[{label}] failed to start claude: {e}", file=sys.stderr)
        return False

    start = time.time()
    last_activity = [start]
    done = threading.Event()
    rate_limited = [False]

    def reader():
        for line in proc.stdout:
            if _RATE_LIMIT_MARKER in line:
                rate_limited[0] = True
            print(f"[{label}] {line}", end="")
            last_activity[0] = time.time()
        done.set()

    def heartbeat():
        while not done.wait(timeout=30):
            elapsed = int(time.time() - start)
            idle = int(time.time() - last_activity[0])
            print(f"[{label}] {elapsed}s elapsed — last activity {idle}s ago", file=sys.stderr)

    t_reader = threading.Thread(target=reader, daemon=True)
    t_beat   = threading.Thread(target=heartbeat, daemon=True)
    t_reader.start()
    t_beat.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"[{label}] timed out after {timeout}s", file=sys.stderr)
        return False
    finally:
        done.set()

    t_reader.join(timeout=5)

    if rate_limited[0]:
        raise RateLimitError(_RATE_LIMIT_MARKER)

    if proc.returncode != 0:
        print(f"[{label}] claude exited {proc.returncode}", file=sys.stderr)
        return False

    return True
