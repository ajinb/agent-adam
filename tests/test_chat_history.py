"""The stored history must stay valid for the next turn, however a turn ends.

Issue #24: a turn that ended with an unanswered tool_use left a history the API
rejects, so every later message failed until the user cleared the chat.
"""

import json

import anthropic
import httpx2
import pytest

import chatbot

TEXT = {"type": "text", "text": "All done."}
TOOL_USE = {"type": "tool_use", "id": "toolu_1", "name": "get_tasks", "input": {}}
THINKING = {"type": "thinking", "thinking": "", "signature": "sig"}


class Store:
    def get_tasks(self, status=None, project=None):
        return []


def reply(content, stop_reason):
    return httpx2.Response(200, json={
        "id": "m", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
        "content": content, "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    })


def api_would_reject(messages):
    """Why the Messages API would refuse this history, or None."""
    for i, message in enumerate(messages):
        content = message["content"]
        if not content:
            return f"messages.{i}: content is empty"
        if message["role"] != "assistant":
            continue
        if content[-1]["type"] == "thinking":
            return f"messages.{i}: the final block cannot be thinking"
        calls = {block["id"] for block in content if block["type"] == "tool_use"}
        following = messages[i + 1]["content"] if i + 1 < len(messages) else []
        answered = {
            block["tool_use_id"]
            for block in following
            if isinstance(block, dict) and block["type"] == "tool_result"
        }
        if calls - answered:
            return f"messages.{i}: tool_use ids without tool_result blocks"
    return None


def two_turns(first_turn, max_iterations=chatbot.MAX_TOOL_ITERATIONS):
    """Run a turn from scripted replies, then a follow-up; return both answers and the history."""
    script = iter(first_turn)

    def handler(request):
        why = api_would_reject(json.loads(request.content)["messages"])
        if why:
            return httpx2.Response(400, json={
                "type": "error", "error": {"type": "invalid_request_error", "message": why},
            })
        return next(script, reply([{"type": "text", "text": "Back on track."}], "end_turn"))

    client = anthropic.Anthropic(api_key="t", max_retries=0,
                                 http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    history = [{"role": "user", "content": "what's on my list?"}]
    first, history, _ = chatbot.chat(client, history, Store(), max_iterations=max_iterations)
    history.append({"role": "user", "content": "try again"})
    second, history, _ = chatbot.chat(client, history, Store())
    return first, second, history


@pytest.mark.parametrize("first_turn", [
    pytest.param([reply([TOOL_USE], "tool_use")] * 3, id="step-cap"),
    pytest.param([reply([TOOL_USE], "max_tokens")], id="tool-call-cut-off"),
    pytest.param([reply([THINKING], "max_tokens")], id="thinking-only-cut-off"),
    pytest.param([reply([TOOL_USE], "refusal")], id="refused-mid-call"),
    pytest.param([reply([], "refusal")], id="refused-empty"),
    pytest.param([reply([TOOL_USE], "tool_use"), reply([TEXT], "end_turn")], id="normal-round-trip"),
])
def test_next_turn_still_works(first_turn):
    first, second, _ = two_turns(first_turn, max_iterations=2)

    assert first, "the user should always get some answer"
    assert second == "Back on track."


def test_a_finished_turn_is_kept():
    _, _, history = two_turns([reply([TEXT], "end_turn")])

    assert history[1]["role"] == "assistant"
    assert history[1]["content"][0].text == "All done."
