"""Dynamic AI provider routing."""

from __future__ import annotations

from nexlayer.core.schemas import ModelProvider
from nexlayer.providers.base import AIProvider
from nexlayer.providers.openai_provider import OpenAIProvider
from nexlayer.providers.anthropic_provider import AnthropicProvider
from nexlayer.providers.local_provider import LocalLLMProvider


_REGISTRY: dict[ModelProvider, type[AIProvider]] = {
    ModelProvider.OPENAI: OpenAIProvider,
    ModelProvider.ANTHROPIC: AnthropicProvider,
    ModelProvider.LOCAL: LocalLLMProvider,
}


def get_provider(model: ModelProvider) -> AIProvider:
    """Return an instantiated provider for the requested model."""
    provider_cls = _REGISTRY.get(model)
    if provider_cls is None:
        raise ValueError(f"Unsupported model provider: {model}")
    return provider_cls()
