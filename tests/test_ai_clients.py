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


class FakeReasoningMessage:
    """Simulates a reasoning model that returns content=None with reasoning_content."""
    content = None
    reasoning_content = "Caption from reasoning."


class FakeReasoningChoice:
    message = FakeReasoningMessage()


class FakeReasoningResponse:
    choices = [FakeReasoningChoice()]


class FakeChatCompletionsReasoning:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeReasoningResponse()


class FakeOpenAIClientReasoning:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeChatCompletionsReasoning()})()


def test_nvidia_nim_client_falls_back_to_reasoning_content_when_content_is_none(monkeypatch):
    """Reasoning models return content=None; client should use reasoning_content."""
    openai_client = FakeOpenAIClientReasoning()
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")
    client = NvidiaNimClient(
        model="stepfun-ai/step-3.7-flash",
        openai_client=openai_client,
    )

    caption = client.generate("Write a property caption.")

    assert caption == "Caption from reasoning."


class FakeEmptyMessage:
    content = None
    reasoning_content = None


class FakeEmptyChoice:
    message = FakeEmptyMessage()


class FakeEmptyResponse:
    choices = [FakeEmptyChoice()]


class FakeChatCompletionsEmpty:
    def create(self, **kwargs):
        return FakeEmptyResponse()


class FakeOpenAIClientEmpty:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeChatCompletionsEmpty()})()


def test_nvidia_nim_client_raises_on_empty_content_and_no_reasoning(monkeypatch):
    """When both content and reasoning_content are empty, raise so retry loop can retry."""
    openai_client = FakeOpenAIClientEmpty()
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")
    client = NvidiaNimClient(
        model="stepfun-ai/step-3.7-flash",
        openai_client=openai_client,
    )

    import pytest
    with pytest.raises(ValueError, match="empty content"):
        client.generate("Write a property caption.")


class FakeChatCompletionsProbe:
    def __init__(self):
        self.probe_calls = 0

    def create(self, **kwargs):
        if kwargs.get("max_tokens") == 5:
            raise RuntimeError("network error")
        return type("R", (), {"choices": []})()


class FakeOpenAIClientProbe:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeChatCompletionsProbe()})()


def test_nvidia_nim_probe_returns_false_on_exception(monkeypatch):
    """probe() should return False when the API call fails."""
    openai_client = FakeOpenAIClientProbe()
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")
    client = NvidiaNimClient(
        model="stepfun-ai/step-3.7-flash",
        openai_client=openai_client,
    )

    assert client.probe() is False


class FakeChatCompletionsProbeOk:
    def create(self, **kwargs):
        return type("R", (), {"choices": []})()


class FakeOpenAIClientProbeOk:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeChatCompletionsProbeOk()})()


def test_nvidia_nim_probe_returns_true_on_success(monkeypatch):
    """probe() should return True when the API call succeeds."""
    openai_client = FakeOpenAIClientProbeOk()
    monkeypatch.setenv("NVIDIA_API_KEY", "nim-key")
    client = NvidiaNimClient(
        model="stepfun-ai/step-3.7-flash",
        openai_client=openai_client,
    )

    assert client.probe() is True

