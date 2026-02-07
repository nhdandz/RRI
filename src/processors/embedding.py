"""Embedding Generator using sentence-transformers."""

import torch
from sentence_transformers import SentenceTransformer

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Module-level cache: load model once per process
_model_cache: dict[str, SentenceTransformer] = {}


def _get_device() -> str:
    """Auto-detect best available device: mps (Apple), cuda (NVIDIA), or cpu."""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class EmbeddingGenerator:
    """Generates vector embeddings for text content."""

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = _get_device()

    @property
    def model(self) -> SentenceTransformer:
        if self.model_name not in _model_cache:
            logger.info("Loading embedding model", model=self.model_name, device=self.device)
            _model_cache[self.model_name] = SentenceTransformer(
                self.model_name, device=self.device
            )
        return _model_cache[self.model_name]

    def embed(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        embeddings = self.model.encode(
            texts, normalize_embeddings=True, batch_size=batch_size
        )
        return embeddings.tolist()

    def embed_paper(self, title: str, abstract: str) -> list[float]:
        text = f"{title}\n\n{abstract}"
        return self.embed(text)

    def embed_repo(self, name: str, description: str, readme: str | None = None) -> list[float]:
        parts = [name, description or ""]
        if readme:
            parts.append(readme[:2000])
        text = "\n\n".join(parts)
        return self.embed(text)
