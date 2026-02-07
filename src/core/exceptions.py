class OSINTBaseError(Exception):
    """Base exception for OSINT Research system."""

    def __init__(self, message: str = "", detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class CollectorError(OSINTBaseError):
    """Error during data collection."""


class RateLimitError(CollectorError):
    """Rate limit exceeded."""

    def __init__(self, source: str, retry_after: int | None = None):
        self.source = source
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {source}")


class CircuitBreakerOpen(CollectorError):
    """Circuit breaker is open, source unavailable."""


class ProcessingError(OSINTBaseError):
    """Error during data processing."""


class LLMError(ProcessingError):
    """Error with LLM inference."""


class StorageError(OSINTBaseError):
    """Error with data storage."""


class VectorStoreError(StorageError):
    """Error with vector database."""


class EntityNotFoundError(OSINTBaseError):
    """Entity not found in database."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"{entity_type} not found: {entity_id}")
