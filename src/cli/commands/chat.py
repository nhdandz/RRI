"""rri chat - Interactive RAG REPL."""

from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.cli._async import run

console = Console()


def chat_command(
    cloud: Annotated[bool, typer.Option(help="Use cloud LLM (OpenAI)")] = False,
    no_rerank: Annotated[bool, typer.Option(help="Disable reranking")] = False,
    collection: Annotated[str, typer.Option(help="Vector collection to search")] = "papers",
) -> None:
    """Start interactive RAG chat."""
    run(_chat_loop(cloud, no_rerank, collection))


async def _chat_loop(cloud: bool, no_rerank: bool, collection: str) -> None:
    from src.cli._context import get_embedding_generator, get_llm_client, get_vector_store
    from src.rag.generator import AnswerGenerator
    from src.rag.pipeline import RAGPipeline
    from src.rag.reranker import CrossEncoderReranker
    from src.rag.retriever import HybridRetriever

    # Initialize components
    llm = get_llm_client(cloud=cloud)
    if not llm:
        console.print("[red]LLM client required for chat[/red]")
        raise typer.Exit(1)

    vector_store = get_vector_store()
    embedding_gen = get_embedding_generator()

    if not vector_store or not embedding_gen:
        console.print("[red]Vector store and embedding model required[/red]")
        raise typer.Exit(1)

    retriever = HybridRetriever(
        vector_store=vector_store,
        embedding_model=embedding_gen,
    )

    reranker = None if no_rerank else CrossEncoderReranker()

    generator = AnswerGenerator(llm_client=llm)

    pipeline = RAGPipeline(
        retriever=retriever,
        reranker=reranker,
        generator=generator,
        llm_client=llm,
    )

    mode = "cloud" if cloud else "local"
    rerank_status = "off" if no_rerank else "on"
    console.print(
        Panel(
            f"[bold]RRI Chat[/bold] | LLM: {mode} | Rerank: {rerank_status} | Collection: {collection}\n"
            "Type your question and press Enter. Type [bold]quit[/bold] or [bold]exit[/bold] to leave.",
            border_style="blue",
        )
    )

    while True:
        try:
            question = console.input("\n[bold cyan]You>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break

        try:
            response = await pipeline.query(
                question=question,
                top_k=10,
                rerank_top_k=5,
            )

            console.print()
            console.print(Markdown(response.answer))

            if response.sources:
                console.print("\n[dim]Sources:[/dim]")
                for i, src in enumerate(response.sources, 1):
                    title = src.get("title", "Unknown")
                    url = src.get("url", "")
                    console.print(f"  [dim]{i}. {title}[/dim]" + (f" - {url}" if url else ""))

            console.print(f"\n[dim]Confidence: {response.confidence:.0%}[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    console.print("\n[dim]Goodbye![/dim]")

    if hasattr(llm, "close"):
        await llm.close()
