"""Rich formatting helpers and file writers for CLI output."""

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()

REPORTS_DIR = Path("./reports")


def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def print_papers_table(papers: list[dict]) -> None:
    table = Table(title="Papers", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan", width=16)
    table.add_column("Title", style="bold", max_width=60)
    table.add_column("Authors", max_width=30)
    table.add_column("Date", width=12)
    table.add_column("Categories", width=16)

    for i, p in enumerate(papers, 1):
        authors = p.get("authors", [])
        author_str = ", ".join(
            a.get("name", "") if isinstance(a, dict) else str(a)
            for a in authors[:3]
        )
        if len(authors) > 3:
            author_str += f" +{len(authors) - 3}"

        categories = p.get("categories", [])
        cat_str = ", ".join(categories[:3]) if categories else ""

        table.add_row(
            str(i),
            str(p.get("id", "")),
            str(p.get("title", ""))[:60],
            author_str,
            str(p.get("date", "")),
            cat_str,
        )

    console.print(table)


def print_repos_table(repos: list[dict]) -> None:
    table = Table(title="Repositories", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan", max_width=30)
    table.add_column("Description", max_width=50)
    table.add_column("Stars", width=8, justify="right")
    table.add_column("Language", width=12)

    for i, r in enumerate(repos, 1):
        table.add_row(
            str(i),
            str(r.get("name", "")),
            str(r.get("description", ""))[:50],
            str(r.get("stars", "")),
            str(r.get("language", "")),
        )

    console.print(table)


def print_hf_models_table(models: list[dict]) -> None:
    table = Table(title="HuggingFace Models", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Model ID", style="cyan", max_width=40)
    table.add_column("Pipeline", width=20)
    table.add_column("Downloads", width=12, justify="right")
    table.add_column("Likes", width=8, justify="right")

    for i, m in enumerate(models, 1):
        table.add_row(
            str(i),
            str(m.get("model_id", "")),
            str(m.get("pipeline_tag", "") or ""),
            str(m.get("downloads", "")),
            str(m.get("likes", "")),
        )

    console.print(table)


def print_analysis_panel(
    title: str,
    summary: str,
    classification: dict | None = None,
    entities: dict | None = None,
) -> None:
    parts = [f"[bold]{title}[/bold]\n"]

    parts.append(f"[green]Summary:[/green]\n{summary}\n")

    if classification:
        parts.append(
            f"[green]Topic:[/green] {classification.get('primary_topic', 'N/A')} "
            f"(confidence: {classification.get('confidence', 0):.0%})"
        )
        keywords = classification.get("keywords", [])
        if keywords:
            parts.append(f"[green]Keywords:[/green] {', '.join(keywords)}")

    if entities:
        for key in ("methods", "datasets", "metrics", "tools"):
            items = entities.get(key, [])
            if items:
                parts.append(f"[green]{key.title()}:[/green] {', '.join(items)}")

    console.print(Panel("\n".join(parts), title="Analysis Result", border_style="blue"))


def print_search_results(results: list[dict]) -> None:
    table = Table(title="Search Results", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Score", width=8, justify="right")
    table.add_column("Title", style="bold", max_width=60)
    table.add_column("Source", width=12)

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{r.get('score', 0):.3f}",
            str(r.get('title', r.get('payload', {}).get('title', '')))[:60],
            str(r.get('source_type', r.get('payload', {}).get('source_type', ''))),
        )

    console.print(table)


def create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def write_markdown(path: Path | str, content: str) -> Path:
    path = Path(path)
    if not path.is_absolute():
        ensure_reports_dir()
        path = REPORTS_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    console.print(f"[green]Written:[/green] {path}")
    return path


def write_json(path: Path | str, data: dict | list) -> Path:
    path = Path(path)
    if not path.is_absolute():
        ensure_reports_dir()
        path = REPORTS_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    console.print(f"[green]Written:[/green] {path}")
    return path
