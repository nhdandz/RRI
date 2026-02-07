"""Paper-Code Linking Processor."""

import re
from dataclasses import dataclass
from datetime import date

from rapidfuzz import fuzz

from src.collectors.github import GitHubCollector
from src.collectors.huggingface import HuggingFaceCollector
from src.collectors.papers_with_code import PapersWithCodeCollector
from src.core.constants import LinkType
from src.core.logging import get_logger

logger = get_logger(__name__)

GITHUB_URL_PATTERN = re.compile(
    r"github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)", re.IGNORECASE
)
ARXIV_ID_PATTERN = re.compile(r"arxiv[:\s]*(\d{4}\.\d{4,5})", re.IGNORECASE)


@dataclass
class LinkEvidence:
    author_name_match: float = 0.0
    readme_contains_arxiv: bool = False
    readme_contains_title: bool = False
    papers_with_code_link: bool = False
    huggingface_link: bool = False
    timing_score: float = 0.0
    github_in_pdf: bool = False

    def calculate_confidence(self) -> float:
        score = 0.0
        if self.papers_with_code_link:
            score += 0.25
        if self.huggingface_link:
            score += 0.25
        if self.github_in_pdf:
            score += 0.20
        score += self.author_name_match * 0.15
        if self.readme_contains_arxiv:
            score += 0.15
        score += self.timing_score * 0.10
        if self.readme_contains_title:
            score += 0.05
        return min(1.0, score)

    def determine_link_type(self) -> LinkType:
        confidence = self.calculate_confidence()
        if confidence >= 0.8:
            return LinkType.OFFICIAL
        elif confidence >= 0.5:
            return LinkType.COMMUNITY
        elif confidence >= 0.3:
            return LinkType.INFERRED
        return LinkType.MENTIONED


@dataclass
class PaperCodeLink:
    paper_id: str
    repo_id: str
    link_type: LinkType
    confidence: float
    evidence: LinkEvidence
    discovered_via: str


class PaperCodeLinker:
    """Finds and validates links between papers and code repositories."""

    def __init__(
        self,
        github_collector: GitHubCollector,
        hf_collector: HuggingFaceCollector,
        pwc_client: PapersWithCodeCollector,
    ):
        self.github = github_collector
        self.hf = hf_collector
        self.pwc = pwc_client

    async def find_repos_for_paper(
        self,
        paper_id: str,
        arxiv_id: str | None,
        title: str,
        authors: list[dict],
        published_date: date | None = None,
    ) -> list[PaperCodeLink]:
        import asyncio

        links = []

        results = await asyncio.gather(
            self._search_papers_with_code(paper_id, arxiv_id),
            self._search_huggingface(paper_id, arxiv_id, authors),
            self._search_github_readme(paper_id, arxiv_id, title, authors),
            return_exceptions=True,
        )

        seen_repos: set[str] = set()
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Link search failed", error=str(result))
                continue
            for link in result:
                if link.repo_id not in seen_repos:
                    seen_repos.add(link.repo_id)
                    links.append(link)

        links.sort(key=lambda x: x.confidence, reverse=True)
        return links

    async def _search_papers_with_code(
        self, paper_id: str, arxiv_id: str | None
    ) -> list[PaperCodeLink]:
        if not arxiv_id:
            return []
        try:
            pwc_data = await self.pwc.get_paper(arxiv_id)
            if not pwc_data or not pwc_data.get("repositories"):
                return []

            links = []
            for repo_data in pwc_data["repositories"]:
                evidence = LinkEvidence(papers_with_code_link=True)
                links.append(
                    PaperCodeLink(
                        paper_id=paper_id,
                        repo_id=repo_data.get("url", ""),
                        link_type=evidence.determine_link_type(),
                        confidence=evidence.calculate_confidence(),
                        evidence=evidence,
                        discovered_via="papers_with_code",
                    )
                )
            return links
        except Exception as e:
            logger.warning("PWC search failed", error=str(e))
            return []

    async def _search_huggingface(
        self,
        paper_id: str,
        arxiv_id: str | None,
        authors: list[dict],
    ) -> list[PaperCodeLink]:
        if not arxiv_id:
            return []
        try:
            models = await self.hf.get_models_for_paper(arxiv_id)
            links = []
            for model in models:
                evidence = LinkEvidence(huggingface_link=True)
                if authors:
                    evidence.author_name_match = _fuzzy_author_match(
                        authors, model.author
                    )
                links.append(
                    PaperCodeLink(
                        paper_id=paper_id,
                        repo_id=f"huggingface:{model.model_id}",
                        link_type=evidence.determine_link_type(),
                        confidence=evidence.calculate_confidence(),
                        evidence=evidence,
                        discovered_via="huggingface",
                    )
                )
            return links
        except Exception as e:
            logger.warning("HF search failed", error=str(e))
            return []

    async def _search_github_readme(
        self,
        paper_id: str,
        arxiv_id: str | None,
        title: str,
        authors: list[dict],
    ) -> list[PaperCodeLink]:
        links = []
        queries = []
        if arxiv_id:
            queries.append(f'"{arxiv_id}" in:readme')

        title_query = title[:50].replace('"', "")
        queries.append(f'"{title_query}" in:readme')

        for query in queries:
            try:
                async for result in self.github.search(
                    query=query, max_results=10
                ):
                    repo = result.data
                    evidence = LinkEvidence()

                    if repo.readme_content and arxiv_id:
                        if arxiv_id in repo.readme_content:
                            evidence.readme_contains_arxiv = True
                    if repo.readme_content:
                        if title.lower()[:30] in repo.readme_content.lower():
                            evidence.readme_contains_title = True
                    if authors:
                        evidence.author_name_match = _fuzzy_author_match(
                            authors, repo.owner
                        )

                    if evidence.calculate_confidence() > 0.2:
                        links.append(
                            PaperCodeLink(
                                paper_id=paper_id,
                                repo_id=repo.full_name,
                                link_type=evidence.determine_link_type(),
                                confidence=evidence.calculate_confidence(),
                                evidence=evidence,
                                discovered_via="github_search",
                            )
                        )
            except Exception as e:
                logger.warning("GitHub search failed", error=str(e))

        return links


def _fuzzy_author_match(paper_authors: list[dict], github_user: str) -> float:
    github_user_lower = github_user.lower()
    best_score = 0.0
    for author in paper_authors:
        name = author.get("name", "").lower()
        score = fuzz.ratio(name, github_user_lower) / 100
        parts = name.split()
        if parts:
            last_name_score = fuzz.ratio(parts[-1], github_user_lower) / 100
            score = max(score, last_name_score)
        best_score = max(best_score, score)
    return best_score


def _calculate_timing_score(paper_date: date, repo_date: date) -> float:
    days_diff = (repo_date - paper_date).days
    if days_diff < 0:
        return max(0, 0.5 + days_diff / 60)
    elif days_diff <= 30:
        return 1.0
    elif days_diff <= 90:
        return 0.8
    elif days_diff <= 180:
        return 0.5
    return 0.2
