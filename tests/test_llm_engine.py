"""Tests for factory/llm_engine.py — _parse_result and RateLimitError."""
import json
import pytest

from factory.llm_engine import _parse_result, RateLimitError


def _wrap(content):
    """Build a claude --output-format json result wrapper."""
    return json.dumps({"type": "result", "result": content})


class TestParseResult:
    def test_extracts_result_from_wrapper(self):
        assert _parse_result(_wrap("hello world")) == "hello world"

    def test_falls_back_to_raw_when_no_wrapper(self):
        assert _parse_result("just plain text") == "just plain text"

    def test_parses_json_object_schema(self):
        result = _parse_result(_wrap(json.dumps({"key": "value"})), schema={"type": "object"})
        assert result == {"key": "value"}

    def test_parses_json_array_schema(self):
        result = _parse_result(_wrap(json.dumps([1, 2, 3])), schema={"type": "array"})
        assert result == [1, 2, 3]

    def test_strips_markdown_fences(self):
        inner = "```json\n{\"a\": 1}\n```"
        result = _parse_result(_wrap(inner), schema={"type": "object"})
        assert result == {"a": 1}

    def test_finds_json_object_embedded_in_text(self):
        inner = 'Here is the result: {"x": 42} — done.'
        result = _parse_result(_wrap(inner), schema={"type": "object"})
        assert result == {"x": 42}

    def test_finds_json_array_embedded_in_text(self):
        result = _parse_result(_wrap("Result: [1, 2, 3]"), schema={"type": "array"})
        assert result == [1, 2, 3]

    def test_picks_result_type_from_multiple_json_objects(self):
        other = json.dumps({"type": "tool_use", "content": "something"})
        result_obj = json.dumps({"type": "result", "result": "done"})
        assert _parse_result(other + "\n" + result_obj) == "done"


class TestRateLimitError:
    def test_is_exception(self):
        with pytest.raises(RateLimitError):
            raise RateLimitError("rate limited")

    def test_is_catchable_as_base_exception(self):
        caught = False
        try:
            raise RateLimitError("x")
        except Exception:
            caught = True
        assert caught
