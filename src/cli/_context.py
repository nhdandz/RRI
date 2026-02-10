"""Factory functions for CLI dependencies."""

from rich.console import Console

from src.core.config import Settings, get_settings

console = Console(stderr=True)


def get_cli_settings() -> Settings:
    return get_settings()


def get_session_factory():
    """Create async session factory. Returns None if DB is unavailable."""
    try:
        from src.storage.database import create_async_session_factory

        return create_async_session_factory()
    except Exception as e:
        console.print(f"[yellow]Warning: Database unavailable ({e})[/yellow]")
        return None


def get_llm_client(cloud: bool = False):
    """Get LLM client. Returns None if unavailable."""
    settings = get_cli_settings()
    try:
        if cloud:
            if not settings.OPENAI_API_KEY:
                console.print("[yellow]Warning: OPENAI_API_KEY not set[/yellow]")
                return None
            from src.llm.openai_client import OpenAIClient

            return OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.CLOUD_LLM_MODEL,
            )
        else:
            from src.llm.ollama_client import OllamaClient

            return OllamaClient(
                base_url=settings.LOCAL_LLM_URL,
                model=settings.LOCAL_LLM_MODEL,
            )
    except Exception as e:
        console.print(f"[yellow]Warning: LLM client unavailable ({e})[/yellow]")
        return None


def get_vector_store():
    """Get vector store. Returns None if unavailable."""
    try:
        from src.storage.vector.qdrant_client import VectorStore

        return VectorStore()
    except Exception as e:
        console.print(f"[yellow]Warning: Vector store unavailable ({e})[/yellow]")
        return None


def get_embedding_generator():
    """Get embedding generator. Returns None if unavailable."""
    try:
        from src.processors.embedding import EmbeddingGenerator

        return EmbeddingGenerator()
    except Exception as e:
        console.print(f"[yellow]Warning: Embedding model unavailable ({e})[/yellow]")
        return None
