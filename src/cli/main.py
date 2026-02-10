"""RRI - OSINT Research Intelligence CLI."""

import typer

from src.cli.commands import analyze, chat, collect, export, search

app = typer.Typer(
    name="rri",
    help="RRI - OSINT Research Intelligence CLI",
    no_args_is_help=True,
)

app.add_typer(collect.app, name="collect", help="Collect papers, models, and repos")
app.add_typer(search.app, name="search", help="Search papers, vectors, and repos")
app.add_typer(analyze.app, name="analyze", help="Analyze papers with LLM")
app.add_typer(export.app, name="export", help="Export reports and data")
app.command(name="chat")(chat.chat_command)


if __name__ == "__main__":
    app()
