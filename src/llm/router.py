"""LLM Router - routes requests to appropriate LLM with auto-fallback."""

from src.core.config import get_settings
from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.llm.ollama_client import OllamaClient
from src.llm.openai_client import OpenAIClient

logger = get_logger(__name__)


class LLMRouter(BaseLLMClient):
    """Routes LLM requests to local or cloud LLMs with automatic fallback.

    If the primary (local) LLM fails, automatically retries with the cloud LLM.
    """

    def __init__(self):
        settings = get_settings()
        self.local_llm = OllamaClient(
            base_url=settings.LOCAL_LLM_URL,
            model=settings.LOCAL_LLM_MODEL,
        )
        self.cloud_llm: BaseLLMClient | None = None
        if settings.OPENAI_API_KEY:
            self.cloud_llm = OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.CLOUD_LLM_MODEL,
            )

    def get_client(self, use_cloud: bool = False) -> BaseLLMClient:
        if use_cloud and self.cloud_llm:
            return self.cloud_llm
        return self.local_llm

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> str:
        # Try local LLM first
        try:
            return await self.local_llm.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.warning("Local LLM failed, attempting fallback", error=str(e))
            if self.cloud_llm:
                logger.info("Falling back to cloud LLM")
                return await self.cloud_llm.generate(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                )
            raise

    async def generate_json(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> dict:
        try:
            return await self.local_llm.generate_json(
                prompt, max_tokens=max_tokens, temperature=temperature
            )
        except Exception as e:
            logger.warning("Local LLM JSON failed, attempting fallback", error=str(e))
            if self.cloud_llm:
                logger.info("Falling back to cloud LLM for JSON")
                return await self.cloud_llm.generate_json(
                    prompt, max_tokens=max_tokens, temperature=temperature
                )
            raise

    async def health_check(self) -> bool:
        local_ok = await self.local_llm.health_check()
        if local_ok:
            return True
        if self.cloud_llm:
            return await self.cloud_llm.health_check()
        return False
