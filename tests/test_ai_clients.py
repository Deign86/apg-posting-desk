import pytest

from apg_automation.ai_clients import NvidiaNimClient, build_ai_client


class FakeChatCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        class Choice:
            message = type("Message", (), {"content": "Professional property caption."})

        return type("Response", (), {"choices": [Choice()]})


class FakeOpenAIClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeChatCompletions()})()


def test_nvidia_nim_client_uses_chat_completions_endpoint(monkeypatch):
    openai_client = FakeOpenAIClient()
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")
    client = NvidiaNimClient(
        model="stepfun-ai/step-3.7-flash",
        openai_client=openai_client,
    )

    caption = client.generate("Write a property caption.")

    assert caption == "Professional property caption."
    assert openai_client.chat.completions.calls == [
        {
            "model": "stepfun-ai/step-3.7-flash",
            "messages": [{"role": "user", "content": "Write a property caption."}],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
    ]


def test_nvidia_nim_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
        NvidiaNimClient(model="stepfun-ai/step-3.7-flash")


def test_build_ai_client_defaults_to_nvidia_nim(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")

    client = build_ai_client("nvidia-nim", "stepfun-ai/step-3.7-flash")

    assert isinstance(client, NvidiaNimClient)
