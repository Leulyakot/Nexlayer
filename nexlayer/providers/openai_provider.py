"""OpenAI provider adapter."""

from __future__ import annotations

import httpx

from nexlayer.config.settings import get_settings
from nexlayer.providers.base import AIProvider, ProviderResponse


class OpenAIProvider(AIProvider):
    """Adapter for the OpenAI chat completions API."""

    ENDPOINT = "https://api.openai.com/v1/chat/completions"

    def provider_name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        model = kwargs.get("model", "gpt-4o")
        max_tokens = kwargs.get("max_tokens", 1024)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return ProviderResponse(
            text=choice,
            model=data.get("model", model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw=data,
        )
