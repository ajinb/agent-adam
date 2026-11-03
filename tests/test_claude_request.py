"""The chat loop's request shape, checked through the real SDK with a mock transport."""

import json

import anthropic
import httpx2

import chatbot


class Store:
    pass


def test_request_uses_caching_fallback_and_current_model():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx2.Response(200, json={
            "id": "m", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": "You have 2 meetings today."}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        })

    client = anthropic.Anthropic(api_key="t", max_retries=0,
                                 http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    text, messages, pending = chatbot.chat(client, [{"role": "user", "content": "today?"}], Store())
    assert text == "You have 2 meetings today."
    body = seen[0]
    assert body["model"] == "claude-sonnet-5-5"
    assert body["cache_control"] == {"type": "ephemeral"}
    assert body["fallbacks"] == "default"
    assert "temperature" not in body
