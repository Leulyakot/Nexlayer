"""Tests for provider routing."""

import pytest

from nexlayer.core.schemas import ModelProvider
from nexlayer.providers.router import get_provider
from nexlayer.providers.openai_provider import OpenAIProvider
from nexlayer.providers.anthropic_provider import AnthropicProvider
from nexlayer.providers.local_provider import LocalLLMProvider


def test_get_openai_provider():
    provider = get_provider(ModelProvider.OPENAI)
    assert isinstance(provider, OpenAIProvider)
    assert provider.provider_name() == "openai"


def test_get_anthropic_provider():
    provider = get_provider(ModelProvider.ANTHROPIC)
    assert isinstance(provider, AnthropicProvider)
    assert provider.provider_name() == "anthropic"


def test_get_local_provider():
    provider = get_provider(ModelProvider.LOCAL)
    assert isinstance(provider, LocalLLMProvider)
    assert provider.provider_name() == "local"
