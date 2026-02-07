"""
GitHub GraphQL API Collector

API Docs: https://docs.github.com/en/graphql
Rate Limit: 5000 points/hour (authenticated)
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)

REPO_QUERY = """
query($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        id
        databaseId
        nameWithOwner
        name
        owner { login }
        description
        url
        homepageUrl
        stargazerCount
        forkCount
        watchers { totalCount }
        primaryLanguage { name }
        languages(first: 10) {
          edges { size node { name } }
        }
        repositoryTopics(first: 20) {
          nodes { topic { name } }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) {
                totalCount
                nodes { committedDate }
              }
            }
          }
        }
        releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes { tagName publishedAt }
        }
        licenseInfo { spdxId }
        hasIssuesEnabled
        openIssues: issues(states: OPEN) { totalCount }
        createdAt
        updatedAt
        pushedAt
      }
    }
  }
  rateLimit { limit cost remaining resetAt }
}
"""


def _parse_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.replace(tzinfo=None)


@dataclass
class GitHubRepo:
    github_id: int
    full_name: str
    name: str
    owner: str
    description: str | None
    html_url: str
    homepage_url: str | None

    stars_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int

    primary_language: str | None
    languages: dict[str, int]
    topics: list[str]

    readme_content: str | None
    has_license: bool
    has_dockerfile: bool
    dependencies: list[str] = field(default_factory=list)

    last_commit_at: datetime | None = None
    last_release_tag: str | None = None
    last_release_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class GitHubCollector(BaseCollector):
    """Collects repositories from GitHub GraphQL API."""

    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: str):
        self.token = token
        super().__init__(
            CollectorConfig(
                name="github",
                base_url=self.GRAPHQL_URL,
                rate_limit_per_minute=80,
            )
        )

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[GitHubRepo]]:
        async for result in self.search(**kwargs):
            yield result

    async def search(
        self,
        query: str | None = None,
        language: str | None = None,
        topics: list[str] | None = None,
        min_stars: int | None = None,
        created_after: date | None = None,
        pushed_after: date | None = None,
        max_results: int = 100,
    ) -> AsyncIterator[CollectorResult[GitHubRepo]]:
        search_query = self._build_search_query(
            query, language, topics, min_stars, created_after, pushed_after
        )

        cursor = None
        collected = 0

        while collected < max_results:
            batch_size = min(25, max_results - collected)

            variables = {
                "query": search_query,
                "first": batch_size,
                "after": cursor,
            }

            response = await self._request(
                "POST",
                self.GRAPHQL_URL,
                json={"query": REPO_QUERY, "variables": variables},
            )

            data = response.json()

            rate_limit = data.get("data", {}).get("rateLimit", {})
            if rate_limit:
                logger.debug(
                    "GitHub rate limit",
                    remaining=rate_limit.get("remaining"),
                    cost=rate_limit.get("cost"),
                )

            search_data = data.get("data", {}).get("search", {})
            nodes = search_data.get("nodes", [])

            if not nodes:
                break

            for node in nodes:
                repo = self._parse_repo(node)
                if repo:
                    yield CollectorResult(
                        data=repo,
                        source="github",
                        collected_at=datetime.utcnow(),
                        raw_response=node,
                    )
                    collected += 1

            page_info = search_data.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")

    async def get_repo(self, owner: str, name: str) -> GitHubRepo | None:
        query = f"repo:{owner}/{name}"
        async for result in self.search(query=query, max_results=1):
            return result.data
        return None

    async def get_trending(
        self,
        language: str | None = None,
        since: str = "daily",
    ) -> AsyncIterator[CollectorResult[GitHubRepo]]:
        days = {"daily": 1, "weekly": 7, "monthly": 30}[since]
        date_from = date.today() - timedelta(days=days)

        async for result in self.search(
            language=language,
            min_stars=50,
            pushed_after=date_from,
            max_results=100,
        ):
            yield result

    def _build_search_query(
        self,
        query: str | None,
        language: str | None,
        topics: list[str] | None,
        min_stars: int | None,
        created_after: date | None,
        pushed_after: date | None,
    ) -> str:
        parts = []
        if query:
            parts.append(query)
        if language:
            parts.append(f"language:{language}")
        if topics:
            for topic in topics:
                parts.append(f"topic:{topic}")
        if min_stars:
            parts.append(f"stars:>={min_stars}")
        if created_after:
            parts.append(f"created:>={created_after.isoformat()}")
        if pushed_after:
            parts.append(f"pushed:>={pushed_after.isoformat()}")
        parts.append("sort:stars")
        return " ".join(parts)

    def _parse_repo(self, node: dict) -> GitHubRepo | None:
        if not node:
            return None

        languages = {}
        for edge in node.get("languages", {}).get("edges") or []:
            languages[edge["node"]["name"]] = edge["size"]

        topics = [
            t["topic"]["name"]
            for t in (node.get("repositoryTopics", {}).get("nodes") or [])
        ]

        dependencies = []

        last_commit_at = None
        branch_ref = node.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target"):
            history = (
                branch_ref["target"].get("history", {}).get("nodes", [])
            )
            if history:
                last_commit_at = _parse_datetime(history[0]["committedDate"])

        releases = node.get("releases", {}).get("nodes", [])
        last_release_tag = releases[0]["tagName"] if releases else None
        last_release_at = (
            _parse_datetime(releases[0]["publishedAt"]) if releases else None
        )

        return GitHubRepo(
            github_id=node["databaseId"],
            full_name=node["nameWithOwner"],
            name=node["name"],
            owner=node["owner"]["login"],
            description=node.get("description"),
            html_url=node["url"],
            homepage_url=node.get("homepageUrl"),
            stars_count=node["stargazerCount"],
            forks_count=node["forkCount"],
            watchers_count=node.get("watchers", {}).get("totalCount", 0),
            open_issues_count=node.get("openIssues", {}).get("totalCount", 0),
            primary_language=(
                node.get("primaryLanguage", {}).get("name")
                if node.get("primaryLanguage")
                else None
            ),
            languages=languages,
            topics=topics,
            readme_content=None,
            has_license=node.get("licenseInfo") is not None,
            has_dockerfile=False,
            dependencies=dependencies,
            last_commit_at=last_commit_at,
            last_release_tag=last_release_tag,
            last_release_at=last_release_at,
            created_at=_parse_datetime(node.get("createdAt")),
            updated_at=_parse_datetime(node.get("updatedAt")),
        )

    def _parse_requirements(self, content: str) -> list[str]:
        deps = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = (
                    line.split("==")[0]
                    .split(">=")[0]
                    .split("<=")[0]
                    .split("[")[0]
                )
                deps.append(pkg.strip())
        return deps

    def _parse_pyproject(self, content: str) -> list[str]:
        deps = []
        in_deps = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("dependencies") and "=" in stripped:
                in_deps = True
                continue
            if in_deps:
                if stripped == "]":
                    break
                pkg = stripped.strip('",').split(">=")[0].split("==")[0].split("[")[0]
                if pkg:
                    deps.append(pkg.strip())
        return deps

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "POST",
                self.GRAPHQL_URL,
                json={"query": "{ viewer { login } }"},
            )
            return "data" in response.json()
        except Exception:
            return False
