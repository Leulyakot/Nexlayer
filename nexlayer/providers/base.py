"""Abstract base for AI model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    """Standardised response from any AI provider."""

    text: str
    model: str
    usage: dict[str, int]  # e.g. {"prompt_tokens": …, "completion_tokens": …}
    raw: dict | None = None  # original provider response for debugging


class AIProvider(ABC):
    """Interface that all provider adapters must implement."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> ProviderResponse:
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...
