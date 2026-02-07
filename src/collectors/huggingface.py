"""
Hugging Face Hub API Collector

API Docs: https://huggingface.co/docs/hub/api
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)


def _parse_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


@dataclass
class HFModel:
    model_id: str
    author: str
    model_name: str
    sha: str
    pipeline_tag: str | None
    tags: list[str]
    downloads: int
    likes: int
    library_name: str | None
    linked_arxiv_ids: list[str]
    created_at: datetime | None = None
    last_modified: datetime | None = None


@dataclass
class HFDataset:
    dataset_id: str
    author: str
    dataset_name: str
    tags: list[str]
    downloads: int
    likes: int
    created_at: datetime | None = None
    last_modified: datetime | None = None


class HuggingFaceCollector(BaseCollector):
    """Collects models and datasets from Hugging Face Hub."""

    BASE_URL = "https://huggingface.co/api"

    def __init__(self, token: str | None = None):
        self.token = token
        super().__init__(
            CollectorConfig(
                name="huggingface",
                base_url=self.BASE_URL,
                rate_limit_per_minute=60,
            )
        )

    def _get_headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[HFModel]]:
        async for result in self.search_models(**kwargs):
            yield result

    async def search_models(
        self,
        query: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        pipeline_tag: str | None = None,
        library: str | None = None,
        arxiv_id: str | None = None,
        sort: str = "downloads",
        direction: str = "-1",
        max_results: int = 100,
    ) -> AsyncIterator[CollectorResult[HFModel]]:
        params: dict = {
            "sort": sort,
            "direction": direction,
            "limit": min(100, max_results),
        }

        if query:
            params["search"] = query
        if author:
            params["author"] = author
        if pipeline_tag:
            params["pipeline_tag"] = pipeline_tag
        if library:
            params["library"] = library
        if tags:
            params["tags"] = ",".join(tags)
        if arxiv_id:
            params["tags"] = f"arxiv:{arxiv_id}"

        response = await self._request(
            "GET", f"{self.BASE_URL}/models", params=params
        )

        for model_data in response.json():
            model = self._parse_model(model_data)
            yield CollectorResult(
                data=model,
                source="huggingface",
                collected_at=datetime.utcnow(),
            )

    async def get_models_for_paper(self, arxiv_id: str) -> list[HFModel]:
        results = []
        async for result in self.search_models(arxiv_id=arxiv_id, max_results=50):
            results.append(result.data)
        return results

    async def get_model(self, model_id: str) -> HFModel | None:
        try:
            response = await self._request(
                "GET", f"{self.BASE_URL}/models/{model_id}"
            )
            return self._parse_model(response.json())
        except Exception:
            return None

    async def search_datasets(
        self,
        query: str | None = None,
        sort: str = "downloads",
        max_results: int = 100,
    ) -> AsyncIterator[CollectorResult[HFDataset]]:
        params: dict = {
            "sort": sort,
            "direction": "-1",
            "limit": min(100, max_results),
        }
        if query:
            params["search"] = query

        response = await self._request(
            "GET", f"{self.BASE_URL}/datasets", params=params
        )

        for ds_data in response.json():
            ds_id = ds_data.get("id", "")
            parts = ds_id.split("/")
            yield CollectorResult(
                data=HFDataset(
                    dataset_id=ds_id,
                    author=parts[0] if len(parts) > 1 else "",
                    dataset_name=parts[1] if len(parts) > 1 else parts[0],
                    tags=ds_data.get("tags", []),
                    downloads=ds_data.get("downloads", 0),
                    likes=ds_data.get("likes", 0),
                    created_at=_parse_datetime(ds_data.get("createdAt")),
                    last_modified=_parse_datetime(ds_data.get("lastModified")),
                ),
                source="huggingface",
                collected_at=datetime.utcnow(),
            )

    def _parse_model(self, data: dict) -> HFModel:
        model_id = data.get("modelId") or data.get("id", "")
        parts = model_id.split("/")
        author = parts[0] if len(parts) > 1 else ""
        model_name = parts[1] if len(parts) > 1 else parts[0]

        tags = data.get("tags", [])
        arxiv_ids = [
            tag.replace("arxiv:", "") for tag in tags if tag.startswith("arxiv:")
        ]

        return HFModel(
            model_id=model_id,
            author=author,
            model_name=model_name,
            sha=data.get("sha", ""),
            pipeline_tag=data.get("pipeline_tag"),
            tags=tags,
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            library_name=data.get("library_name"),
            linked_arxiv_ids=arxiv_ids,
            created_at=_parse_datetime(data.get("createdAt")),
            last_modified=_parse_datetime(data.get("lastModified")),
        )

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET", f"{self.BASE_URL}/models", params={"limit": 1}
            )
            return response.status_code == 200
        except Exception:
            return False
