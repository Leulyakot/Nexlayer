"""Anthropic Claude provider adapter."""

from __future__ import annotations

import httpx

from nexlayer.config.settings import get_settings
from nexlayer.providers.base import AIProvider, ProviderResponse


class AnthropicProvider(AIProvider):
    """Adapter for the Anthropic Messages API."""

    ENDPOINT = "https://api.anthropic.com/v1/messages"

    def provider_name(self) -> str:
        return "anthropic"

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        model = kwargs.get("model", "claude-sonnet-4-20250514")
        max_tokens = kwargs.get("max_tokens", 1024)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                self.ENDPOINT,
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        text = data["content"][0]["text"] if data.get("content") else ""
        usage = data.get("usage", {})

        return ProviderResponse(
            text=text,
            model=data.get("model", model),
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            },
            raw=data,
        )
