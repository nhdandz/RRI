"""Paper/Repo Summarization Processor."""

from dataclasses import dataclass

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.llm.prompts.summarization import PAPER_SUMMARY_PROMPT, README_SUMMARY_PROMPT

logger = get_logger(__name__)


@dataclass
class Summary:
    line1: str
    line2: str
    line3: str
    full_text: str

    @classmethod
    def from_lines(cls, lines: list[str]) -> "Summary":
        return cls(
            line1=lines[0] if len(lines) > 0 else "",
            line2=lines[1] if len(lines) > 1 else "",
            line3=lines[2] if len(lines) > 2 else "",
            full_text="\n".join(lines),
        )


class Summarizer:
    """Generates concise summaries for papers and repositories."""

    def __init__(
        self,
        local_llm: BaseLLMClient,
        cloud_llm: BaseLLMClient | None = None,
    ):
        self.local_llm = local_llm
        self.cloud_llm = cloud_llm

    async def summarize_paper(
        self, title: str, abstract: str, use_cloud: bool = False
    ) -> Summary:
        llm = self.cloud_llm if use_cloud and self.cloud_llm else self.local_llm

        prompt = PAPER_SUMMARY_PROMPT.format(
            title=title, abstract=abstract[:3000]
        )

        response = await llm.generate(prompt, max_tokens=300, temperature=0.3)
        return self._parse_summary(response)

    async def summarize_readme(
        self, readme_content: str, use_cloud: bool = False
    ) -> Summary:
        llm = self.cloud_llm if use_cloud and self.cloud_llm else self.local_llm

        truncated = readme_content[:5000]
        prompt = README_SUMMARY_PROMPT.format(readme=truncated)

        response = await llm.generate(prompt, max_tokens=300, temperature=0.3)
        return self._parse_summary(response)

    def _parse_summary(self, response: str) -> Summary:
        lines = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line:
                if ":" in line:
                    line = line.split(":", 1)[1].strip()
                lines.append(line)
        return Summary.from_lines(lines[:3])
