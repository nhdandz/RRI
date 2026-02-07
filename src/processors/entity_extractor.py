"""Entity Extraction Processor - extracts methods, datasets, tools from papers."""

import json
from dataclasses import dataclass, field

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.llm.prompts.extraction import ENTITY_EXTRACTION_PROMPT

logger = get_logger(__name__)


@dataclass
class ExtractedEntities:
    methods: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


class EntityExtractor:
    """Extracts key entities from papers using LLM."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    async def extract(self, title: str, abstract: str) -> ExtractedEntities:
        prompt = ENTITY_EXTRACTION_PROMPT.format(
            title=title, abstract=abstract[:2000]
        )

        response = await self.llm.generate(
            prompt, max_tokens=300, temperature=0.1
        )

        try:
            text = response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            data = json.loads(text)
            return ExtractedEntities(
                methods=data.get("methods", []),
                datasets=data.get("datasets", []),
                metrics=data.get("metrics", []),
                tools=data.get("tools", []),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse entity extraction", error=str(e))
            return ExtractedEntities()
