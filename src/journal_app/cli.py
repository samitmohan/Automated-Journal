import argparse
import glob
import logging
import os
import sys
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from journal_app import config
from journal_app.models import Journal
from journal_app.providers.markdown_storage_provider import MarkdownStorageProvider
from journal_app.providers.zen_quote_provider import ZenQuoteProvider

console = Console()
logger = logging.getLogger(__name__)


def build_journal() -> Journal:
    return Journal(
        config.NAMESPACE,
        config.TITLE,
        config.DAY_QUESTIONS,
        config.NIGHT_QUESTIONS,
        config.DEFAULT_TOTAL_ANSWERS,
    )


def build_storage() -> MarkdownStorageProvider:
    return MarkdownStorageProvider(
        config.ROOT_DIR,
        config.OUTPUT_DIR,
        config.HEADER_TEMPLATE,
        config.QUESTION_TEMPLATE,
    )


def compute_streak(output_dir: str, namespace: str) -> int:
    """Walk backwards from today counting consecutive journal entries."""
    streak = 0
    day = datetime.today()
    while True:
        date_str = day.strftime("%Y-%m-%d")
        year_str = str(day.year)
        path = os.path.join(output_dir, year_str, f"{namespace}-{date_str}.md")
        if os.path.exists(path):
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


def ask_question(question):
    """Prompt user for answers to a question using Rich."""
    console.print(f"\n  [bold cyan]{question.content()}[/bold cyan]\n")
    for idx in range(question.total_answers):
        answer_id = idx + 1
        response = Prompt.ask(f"  {answer_id}")
        question.answer(answer_id, response)


def display_quote(quote):
    """Display quote in a Rich panel."""
    if quote.content() and quote.author():
        console.print()
        console.print(Panel(
            f'[italic]"{quote.content()}"[/italic]\n\n[dim]~ {quote.author()}[/dim]',
            border_style="blue",
            padding=(1, 2),
        ))


def display_analysis(analysis):
    """Display post-journaling analysis summary."""
    overall = analysis.overall

    sentiment_color = "green" if overall.sentiment.label == "POSITIVE" else "red"
    label = f"{overall.sentiment.label} ({overall.sentiment.score:.2f})"
    sentiment_text = f"[{sentiment_color}]{label}[/{sentiment_color}]"

    dominant_emotion = overall.emotions.dominant()
    dominant_score = overall.emotions.dominant_score()

    keywords = ", ".join(overall.keywords[:5]) if overall.keywords else "none"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")
    table.add_row("Sentiment", sentiment_text)
    table.add_row("Top Emotion", f"{dominant_emotion.capitalize()} ({dominant_score:.2f})")
    table.add_row("Keywords", keywords)

    console.print()
    console.print(Panel(
        table,
        title="[bold]Journal Analysis[/bold]",
        border_style="green",
        padding=(1, 2),
    ))


def cmd_journal():
    """Interactive journaling - the default command."""
    journal = build_journal()
    storage = build_storage()
    quote = ZenQuoteProvider()

    streak = compute_streak(config.OUTPUT_DIR, config.NAMESPACE)
    if streak > 0:
        console.print(f"\n  [dim]Current streak: {streak} day(s)[/dim]")

    if storage.filled_twice(journal):
        console.print(f"\n  [yellow]{config.MESSAGES.get('complete')}[/yellow]\n")
        return

    is_evening = storage.filled_once(journal)

    console.print(f"\n  [bold]{journal.header_title()}[/bold]")

    if is_evening:
        questions = journal.night_questions()
    else:
        quote.load()
        display_quote(quote)
        questions = journal.day_questions()

    for question in questions:
        ask_question(question)

    storage.save(journal, quote)
    filepath = storage.file_path(journal)
    console.print(f"\n  [green]{config.MESSAGES.get('saved')}: {filepath}[/green]")

    # Run NLP analysis
    try:
        from journal_app.analysis.analyzer import JournalAnalyzer
        console.print("\n  [dim]Analyzing entry...[/dim]")
        analyzer = JournalAnalyzer()
        analysis = analyzer.analyze_file(filepath)
        storage.save_analysis(filepath, analysis.to_dict())
        display_analysis(analysis)
    except Exception as e:
        logger.debug("Analysis failed: %s", e)
        console.print("\n  [dim]Analysis skipped (models not available)[/dim]")

    streak = compute_streak(config.OUTPUT_DIR, config.NAMESPACE)
    if streak > 0:
        console.print(f"\n  [dim]Streak: {streak} day(s)[/dim]\n")


def cmd_analyze(force: bool = False):
    """Batch analyze all journal entries."""
    storage = build_storage()

    pattern = os.path.join(config.OUTPUT_DIR, "**", f"{config.NAMESPACE}-*.md")
    files = sorted(glob.glob(pattern, recursive=True))

    if not files:
        console.print("\n  [yellow]No journal entries found.[/yellow]\n")
        return

    try:
        from journal_app.analysis.analyzer import JournalAnalyzer
    except ImportError:
        console.print("\n  [red]Analysis dependencies not installed.[/red]\n")
        return

    analyzer = JournalAnalyzer()
    analyzed = 0
    skipped = 0

    for filepath in files:
        analysis_path = storage.analysis_path(filepath)
        if os.path.exists(analysis_path) and not force:
            skipped += 1
            continue

        console.print(f"  Analyzing: [cyan]{os.path.basename(filepath)}[/cyan]")
        try:
            analysis = analyzer.analyze_file(filepath)
            storage.save_analysis(filepath, analysis.to_dict())
            analyzed += 1
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")

    console.print(f"\n  [green]Done:[/green] {analyzed} analyzed, {skipped} skipped\n")


def cmd_stats():
    """Display journal statistics."""
    pattern = os.path.join(config.OUTPUT_DIR, "**", f"{config.NAMESPACE}-*.md")
    files = sorted(glob.glob(pattern, recursive=True))

    streak = compute_streak(config.OUTPUT_DIR, config.NAMESPACE)

    table = Table(title="Journal Stats", show_header=False, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Total Entries", str(len(files)))
    table.add_row("Current Streak", f"{streak} day(s)")

    # Load analysis data for sentiment stats
    analysis_files = sorted(glob.glob(
        os.path.join(config.OUTPUT_DIR, "**", "*.analysis.json"),
        recursive=True,
    ))

    if analysis_files:
        import json
        scores = []
        for af in analysis_files:
            try:
                with open(af) as f:
                    data = json.load(f)
                scores.append(data["overall"]["sentiment"]["score"])
            except Exception:
                pass

        if scores:
            avg = sum(scores) / len(scores)
            color = "green" if avg > 0.6 else "yellow" if avg > 0.4 else "red"
            table.add_row("Avg Sentiment", f"[{color}]{avg:.2f}[/{color}]")
            table.add_row("Entries Analyzed", str(len(scores)))

    console.print()
    console.print(table)
    console.print()


def cmd_dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = os.path.join(
        os.path.dirname(__file__), "dashboard", "app.py"
    )
    console.print("\n  [bold]Launching dashboard...[/bold]\n")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered journaling CLI with NLP analysis",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("journal", help="Interactive journaling (default)")

    analyze_parser = subparsers.add_parser("analyze", help="Batch analyze all entries")
    analyze_parser.add_argument(
        "--force", action="store_true", help="Re-analyze existing entries"
    )

    subparsers.add_parser("stats", help="Display journal statistics")
    subparsers.add_parser("dashboard", help="Launch Streamlit dashboard")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(force=args.force)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "dashboard":
        cmd_dashboard()
    else:
        cmd_journal()


if __name__ == "__main__":
    main()
