import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.exceptions import CircuitBreakerOpen, RateLimitError
from src.core.logging import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


@dataclass
class CollectorConfig:
    name: str
    base_url: str
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class CollectorResult(Generic[T]):
    data: T
    source: str
    collected_at: datetime
    raw_response: dict | None = None


class RateLimiter:
    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.interval = 60.0 / max_per_minute
        self._last_request: float = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self._last_request = time.monotonic()


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._is_open = False

    def can_execute(self) -> bool:
        if not self._is_open:
            return True
        if time.monotonic() - self._last_failure_time > self.recovery_timeout:
            self._is_open = False
            self._failure_count = 0
            return True
        return False

    def record_success(self) -> None:
        self._failure_count = 0
        self._is_open = False

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._is_open = True
            logger.warning(
                "Circuit breaker opened",
                failure_count=self._failure_count,
            )


class BaseCollector(ABC):
    """Abstract base class for all collectors."""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self.client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60
        )

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            headers=self._get_headers(),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    @abstractmethod
    def _get_headers(self) -> dict:
        pass

    @abstractmethod
    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult]:
        pass
        yield  # Make it a generator  # noqa: E501

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=120),
    )
    async def _request(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        await self._rate_limiter.acquire()

        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpen(f"Circuit open for {self.config.name}")

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            self._circuit_breaker.record_success()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(
                    "Rate limited, waiting",
                    source=self.config.name,
                    retry_after=retry_after,
                )
                await asyncio.sleep(retry_after)
                raise  # let tenacity retry after sleeping
            self._circuit_breaker.record_failure()
            raise
        except Exception:
            self._circuit_breaker.record_failure()
            raise
