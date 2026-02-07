import json

from openai import AsyncOpenAI

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """Cloud LLM client using OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def generate_json(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> dict:
        text = await self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt="You must respond with valid JSON only.",
        )
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI JSON response", response=text[:200])
            return {}

    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
