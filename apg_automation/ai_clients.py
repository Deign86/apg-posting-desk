from __future__ import annotations

import os

NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_NIM_MODEL = "stepfun-ai/step-3.7-flash"


class NvidiaNimClient:
    def __init__(
        self,
        *,
        model: str = DEFAULT_NVIDIA_NIM_MODEL,
        api_key: str | None = None,
        openai_client=None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NVIDIA NIM captions")
        if openai_client is None:
            from openai import OpenAI

            openai_client = OpenAI(
                base_url=NVIDIA_NIM_BASE_URL,
                api_key=self.api_key,
            )
        self.client = openai_client

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200,
        )
        return response.choices[0].message.content


class OpenAIClient:
    def __init__(self, *, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )
        return response.output_text


class AnthropicClient:
    def __init__(self, *, model: str) -> None:
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )


def build_ai_client(provider: str, model: str):
    provider_key = provider.lower()
    if provider_key in {"nvidia", "nvidia-nim", "nim"}:
        return NvidiaNimClient(model=model)
    if provider_key == "openai":
        return OpenAIClient(model=model)
    if provider_key in {"anthropic", "claude"}:
        return AnthropicClient(model=model)
    raise ValueError(f"Unsupported AI provider: {provider}")
