from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict | None = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
