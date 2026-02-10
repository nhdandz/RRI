"""rri analyze - Analyze papers with LLM."""

from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, Optional

import typer

from src.cli._async import run
from src.cli._output import (
    console,
    create_progress,
    print_analysis_panel,
    write_json,
    write_markdown,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def paper(
    arxiv_id: Annotated[str, typer.Argument(help="ArXiv paper ID (e.g. 2401.12345)")],
    cloud: Annotated[bool, typer.Option(help="Use cloud LLM (OpenAI)")] = False,
    output: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
    save_db: Annotated[bool, typer.Option(help="Save analysis to database")] = False,
) -> None:
    """Analyze a single paper by ArXiv ID."""
    run(_analyze_paper(arxiv_id, cloud, output, save_db))


async def _analyze_paper(
    arxiv_id: str,
    cloud: bool,
    output: Path | None,
    save_db: bool,
) -> None:
    from src.cli._context import get_llm_client
    from src.collectors.arxiv import ArxivCollector

    # Fetch paper
    console.print(f"Fetching paper [cyan]{arxiv_id}[/cyan]...")
    paper_data = None
    async with ArxivCollector() as collector:
        async for result in collector.collect(
            search_query=f"id:{arxiv_id}",
            max_results=5,
        ):
            if result.data.arxiv_id.endswith(arxiv_id) or arxiv_id in result.data.arxiv_id:
                paper_data = result.data
                break

    if not paper_data:
        console.print(f"[red]Paper {arxiv_id} not found[/red]")
        raise typer.Exit(1)

    console.print(f"Found: [bold]{paper_data.title}[/bold]")

    # Get LLM client
    llm = get_llm_client(cloud=cloud)
    if not llm:
        console.print("[red]LLM client required for analysis[/red]")
        raise typer.Exit(1)

    analysis = await _run_analysis(llm, paper_data.title, paper_data.abstract)

    print_analysis_panel(
        title=paper_data.title,
        summary=analysis["summary"],
        classification=analysis["classification"],
        entities=analysis["entities"],
    )

    if save_db:
        await _save_analysis_to_db(arxiv_id, analysis)

    if output is not None or True:
        out_dir = output or Path("./reports")
        _write_analysis_report(out_dir, arxiv_id, paper_data, analysis)

    if hasattr(llm, "close"):
        await llm.close()


async def _run_analysis(llm, title: str, abstract: str) -> dict:
    from src.processors.classifier import TopicClassifier
    from src.processors.entity_extractor import EntityExtractor
    from src.processors.summarizer import Summarizer

    analysis = {"summary": "", "classification": None, "entities": None}

    with create_progress() as progress:
        task = progress.add_task("Analyzing paper...", total=3)

        # Summarize
        summarizer = Summarizer(local_llm=llm)
        summary = await summarizer.summarize_paper(title, abstract)
        analysis["summary"] = summary.full_text
        progress.update(task, advance=1)

        # Classify
        classifier = TopicClassifier(llm_client=llm)
        classification = await classifier.classify(title, abstract)
        analysis["classification"] = {
            "primary_topic": str(classification.primary_topic.value)
            if hasattr(classification.primary_topic, "value")
            else str(classification.primary_topic),
            "confidence": classification.confidence,
            "keywords": classification.keywords,
        }
        progress.update(task, advance=1)

        # Extract entities
        extractor = EntityExtractor(llm_client=llm)
        entities = await extractor.extract(title, abstract)
        analysis["entities"] = {
            "methods": entities.methods,
            "datasets": entities.datasets,
            "metrics": entities.metrics,
            "tools": entities.tools,
        }
        progress.update(task, advance=1)

    return analysis


async def _save_analysis_to_db(arxiv_id: str, analysis: dict) -> None:
    from src.cli._context import get_session_factory
    from src.storage.repositories.paper_repo import PaperRepository

    factory = get_session_factory()
    if not factory:
        return

    async with factory() as session:
        repo = PaperRepository(session)
        paper = await repo.get_by_arxiv_id(arxiv_id)
        if paper:
            paper.summary = analysis["summary"]
            if analysis["classification"]:
                paper.primary_topic = analysis["classification"]["primary_topic"]
                paper.keywords = analysis["classification"]["keywords"]
            if analysis["entities"]:
                paper.entities = analysis["entities"]
            paper.is_processed = True
            await session.commit()
            console.print("[green]Analysis saved to database[/green]")
        else:
            console.print("[yellow]Paper not found in DB, skipping save[/yellow]")


def _write_analysis_report(out_dir: Path, arxiv_id: str, paper_data, analysis: dict) -> None:
    md = f"# Analysis: {paper_data.title}\n\n"
    md += f"**ArXiv ID:** {arxiv_id}\n"
    md += f"**Authors:** {', '.join(a['name'] for a in paper_data.authors)}\n"
    md += f"**Date:** {paper_data.published_date}\n"
    md += f"**Categories:** {', '.join(paper_data.categories)}\n\n"
    md += f"## Abstract\n{paper_data.abstract}\n\n"
    md += f"## Summary\n{analysis['summary']}\n\n"

    if analysis["classification"]:
        md += f"## Classification\n"
        md += f"- **Topic:** {analysis['classification']['primary_topic']}\n"
        md += f"- **Confidence:** {analysis['classification']['confidence']:.0%}\n"
        md += f"- **Keywords:** {', '.join(analysis['classification']['keywords'])}\n\n"

    if analysis["entities"]:
        md += f"## Entities\n"
        for key, items in analysis["entities"].items():
            if items:
                md += f"- **{key.title()}:** {', '.join(items)}\n"

    write_markdown(out_dir / f"analysis_{arxiv_id.replace('/', '_')}.md", md)
    write_json(out_dir / f"analysis_{arxiv_id.replace('/', '_')}.json", {
        "arxiv_id": arxiv_id,
        "title": paper_data.title,
        **analysis,
    })


@app.command()
def batch(
    query: Annotated[str, typer.Argument(help="Search query for papers")],
    max_results: Annotated[int, typer.Option(help="Maximum papers to analyze")] = 10,
    category: Annotated[Optional[list[str]], typer.Option(help="ArXiv categories")] = None,
    cloud: Annotated[bool, typer.Option(help="Use cloud LLM")] = False,
    output: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
) -> None:
    """Batch analyze papers matching a query."""
    run(_analyze_batch(query, max_results, category, cloud, output))


async def _analyze_batch(
    query: str,
    max_results: int,
    category: list[str] | None,
    cloud: bool,
    output: Path | None,
) -> None:
    from src.cli._context import get_llm_client
    from src.collectors.arxiv import ArxivCollector

    categories = category or ["cs.AI", "cs.CL", "cs.CV", "cs.LG"]
    date_from = date.today() - timedelta(days=30)

    # Collect papers
    papers = []
    async with ArxivCollector() as collector:
        with create_progress() as progress:
            task = progress.add_task("Collecting papers...", total=max_results)
            async for result in collector.collect(
                categories=categories,
                search_query=query,
                date_from=date_from,
                max_results=max_results,
            ):
                papers.append(result.data)
                progress.update(task, advance=1)

    if not papers:
        console.print("[yellow]No papers found[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[green]Collected {len(papers)} papers, starting analysis...[/green]")

    llm = get_llm_client(cloud=cloud)
    if not llm:
        console.print("[red]LLM client required[/red]")
        raise typer.Exit(1)

    all_analyses = []
    with create_progress() as progress:
        task = progress.add_task("Analyzing papers...", total=len(papers))
        for p in papers:
            try:
                analysis = await _run_analysis(llm, p.title, p.abstract)
                analysis["arxiv_id"] = p.arxiv_id
                analysis["title"] = p.title
                all_analyses.append(analysis)

                console.print(f"  [green]✓[/green] {p.arxiv_id}: {p.title[:60]}...")
            except Exception as e:
                console.print(f"  [red]✗[/red] {p.arxiv_id}: {e}")
            progress.update(task, advance=1)

    console.print(f"\n[green]Analyzed {len(all_analyses)}/{len(papers)} papers[/green]")

    out_dir = output or Path("./reports")
    write_json(out_dir / f"batch_analysis_{query.replace(' ', '_')}.json", all_analyses)

    # Write summary markdown
    md = f"# Batch Analysis: {query}\n\n"
    md += f"**Papers analyzed:** {len(all_analyses)}\n"
    md += f"**Categories:** {', '.join(categories)}\n\n"
    for a in all_analyses:
        md += f"## {a.get('title', 'N/A')}\n"
        md += f"**ArXiv:** {a.get('arxiv_id', '')}\n\n"
        md += f"{a.get('summary', '')}\n\n"
        if a.get("classification"):
            md += f"**Topic:** {a['classification']['primary_topic']} | "
            md += f"**Keywords:** {', '.join(a['classification'].get('keywords', []))}\n\n"
        md += "---\n\n"

    write_markdown(out_dir / f"batch_analysis_{query.replace(' ', '_')}.md", md)

    if hasattr(llm, "close"):
        await llm.close()
