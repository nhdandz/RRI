"""Vietnamese word segmentation support."""

from src.core.logging import get_logger

logger = get_logger(__name__)


class VietnameseTokenizer:
    """Vietnamese text tokenizer using underthesea or pyvi."""

    def __init__(self):
        self._tokenizer = None

    def _load(self):
        if self._tokenizer is None:
            try:
                from underthesea import word_tokenize
                self._tokenizer = word_tokenize
            except ImportError:
                logger.warning("underthesea not installed, falling back to basic tokenization")
                self._tokenizer = lambda text: text

    def tokenize(self, text: str) -> str:
        self._load()
        return self._tokenizer(text)

    def tokenize_for_embedding(self, text: str) -> str:
        """Tokenize text specifically for embedding models."""
        return self.tokenize(text)
