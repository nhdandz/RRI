"""Topic Classification Processor."""

import asyncio
import json
from dataclasses import dataclass

from src.core.constants import Topic
from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.llm.prompts.classification import CLASSIFICATION_PROMPT

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    primary_topic: Topic
    secondary_topics: list[Topic]
    confidence: float
    keywords: list[str]


class TopicClassifier:
    """Classifies papers into research topics using LLM."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    async def classify(self, title: str, abstract: str) -> ClassificationResult:
        prompt = CLASSIFICATION_PROMPT.format(
            title=title, abstract=abstract[:2000]
        )

        response = await self.llm.generate(
            prompt, max_tokens=200, temperature=0.1
        )

        try:
            result = json.loads(response)
            return ClassificationResult(
                primary_topic=Topic(result["primary_topic"]),
                secondary_topics=[
                    Topic(t) for t in result.get("secondary_topics", [])
                ],
                confidence=result.get("confidence", 0.5),
                keywords=result.get("keywords", []),
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Failed to parse classification", error=str(e))
            return ClassificationResult(
                primary_topic=Topic.OTHER,
                secondary_topics=[],
                confidence=0.0,
                keywords=[],
            )

    async def classify_batch(
        self, papers: list[tuple[str, str]]
    ) -> list[ClassificationResult]:
        tasks = [self.classify(title, abstract) for title, abstract in papers]
        return await asyncio.gather(*tasks)

    async def is_relevant(
        self, title: str, abstract: str, target_topics: list[Topic]
    ) -> bool:
        result = await self.classify(title, abstract)
        all_topics = [result.primary_topic] + result.secondary_topics
        return any(topic in target_topics for topic in all_topics)
