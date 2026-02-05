"""Local LLM provider stub adapter.

This adapter is a placeholder for connecting to locally-hosted models
(e.g., via Ollama, vLLM, or a custom inference server).
"""

from __future__ import annotations

import httpx

from nexlayer.config.settings import get_settings
from nexlayer.providers.base import AIProvider, ProviderResponse


class LocalLLMProvider(AIProvider):
    """Adapter for a local LLM endpoint (Ollama-compatible API)."""

    def provider_name(self) -> str:
        return "local"

    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        settings = get_settings()
        endpoint = settings.local_llm_endpoint.rstrip("/")
        model = kwargs.get("model", "llama3")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return ProviderResponse(
            text=data.get("response", ""),
            model=model,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            raw=data,
        )
