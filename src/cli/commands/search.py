"""rri search - Search papers, vectors, and repos."""

from typing import Annotated, Optional

import typer

from src.cli._async import run
from src.cli._output import console, print_papers_table, print_search_results

app = typer.Typer(no_args_is_help=True)


@app.command()
def papers(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option(help="Maximum results")] = 20,
    sort_by: Annotated[str, typer.Option(help="Sort by: published_date, citations")] = "published_date",
    category: Annotated[Optional[str], typer.Option(help="Filter by category")] = None,
    source: Annotated[Optional[str], typer.Option(help="Filter by source")] = None,
) -> None:
    """Search papers in database."""
    run(_search_papers(query, limit, sort_by, category, source))


async def _search_papers(
    query: str,
    limit: int,
    sort_by: str,
    category: str | None,
    source: str | None,
) -> None:
    from src.cli._context import get_session_factory
    from src.services.paper_service import PaperService

    factory = get_session_factory()
    if not factory:
        console.print("[red]Database required for paper search[/red]")
        raise typer.Exit(1)

    async with factory() as session:
        svc = PaperService(session)
        filters = {}
        if category:
            filters["category"] = category
        if source:
            filters["source"] = source

        results, total = await svc.list_papers(
            skip=0,
            limit=limit,
            filters={**filters, "search": query} if query else filters,
            sort_by=sort_by,
        )

    console.print(f"\n[green]Found {total} papers (showing {len(results)})[/green]")

    if results:
        paper_dicts = []
        for p in results:
            paper_dicts.append({
                "id": str(p.arxiv_id or p.id),
                "title": p.title,
                "authors": p.authors or [],
                "categories": p.categories or [],
                "date": str(p.published_date or ""),
            })
        print_papers_table(paper_dicts)


@app.command()
def vector(
    query: Annotated[str, typer.Argument(help="Search query for semantic search")],
    limit: Annotated[int, typer.Option(help="Maximum results")] = 10,
    collection: Annotated[str, typer.Option(help="Qdrant collection")] = "papers",
) -> None:
    """Semantic vector search."""
    run(_search_vector(query, limit, collection))


async def _search_vector(query: str, limit: int, collection: str) -> None:
    from src.cli._context import get_embedding_generator, get_vector_store

    embedding_gen = get_embedding_generator()
    vector_store = get_vector_store()

    if not embedding_gen or not vector_store:
        console.print("[red]Embedding model and vector store required[/red]")
        raise typer.Exit(1)

    console.print(f"Embedding query: [cyan]{query}[/cyan]")
    query_vector = embedding_gen.embed(query)

    results = vector_store.search(
        collection=collection,
        query_vector=query_vector,
        limit=limit,
    )

    console.print(f"\n[green]Found {len(results)} results in '{collection}'[/green]")

    if results:
        print_search_results(results)


@app.command()
def repos(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option(help="Maximum results")] = 10,
) -> None:
    """Search repos via vector search."""
    run(_search_vector(query, limit, "repositories"))
