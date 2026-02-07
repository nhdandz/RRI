"""Technology Stack Analyzer for repositories."""

import json

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.llm.prompts.extraction import TECH_ANALYSIS_PROMPT

logger = get_logger(__name__)


class TechAnalyzer:
    """Analyzes technology stack of repositories."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    async def analyze(
        self,
        repo_name: str,
        description: str,
        language: str,
        dependencies: list[str],
    ) -> dict:
        prompt = TECH_ANALYSIS_PROMPT.format(
            repo_name=repo_name,
            description=description or "No description",
            language=language or "Unknown",
            dependencies=", ".join(dependencies[:30]),
        )

        response = await self.llm.generate(
            prompt, max_tokens=300, temperature=0.1
        )

        try:
            text = response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            return json.loads(text)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse tech analysis", error=str(e))
            return {
                "frameworks": [],
                "patterns": [],
                "techniques": [],
                "category": "unknown",
            }
