"""Vietnamese Named Entity Recognition."""

from dataclasses import dataclass

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VietnameseEntity:
    text: str
    label: str
    start: int
    end: int


class VietnameseNER:
    """Vietnamese NER using underthesea."""

    def __init__(self):
        self._ner = None

    def _load(self):
        if self._ner is None:
            try:
                from underthesea import ner
                self._ner = ner
            except ImportError:
                logger.warning("underthesea not installed, NER unavailable")
                self._ner = lambda text: []

    def extract_entities(self, text: str) -> list[VietnameseEntity]:
        self._load()
        try:
            results = self._ner(text)
            entities = []
            pos = 0
            for word, _, _, label in results:
                if label != "O":
                    entities.append(
                        VietnameseEntity(
                            text=word,
                            label=label,
                            start=pos,
                            end=pos + len(word),
                        )
                    )
                pos += len(word) + 1
            return entities
        except Exception as e:
            logger.warning("Vietnamese NER failed", error=str(e))
            return []
