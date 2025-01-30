#!/usr/bin/env python3

import os
import subprocess
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
import yaml
from rich.console import Console
from tqdm import tqdm

app = typer.Typer(help="AI vs. Human Code Contribution Analysis Tool")
console = Console()

DEFAULT_INCLUDE_PATTERNS = [
    "*.js",
    "*.py",
    "*.scm",
    "*.sh",
    "Dockerfile",
    "*.md",
    ".github/workflows/*.yml",
]

DEFAULT_EXCLUDE_PATTERNS = [
    "tests/fixtures/watch/*",
    "**/prompts.py",
]

DEFAULT_AI_COMMITTER = "llm <llm@opioinc.com>"


def run_git_command(cmd: List[str]) -> str:
    """Execute a git command and return its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running git command: {' '.join(cmd)}[/red]")
        console.print(f"[red]Error: {e.stderr}[/red]")
        raise typer.Exit(1)


def get_file_counts(
    start_date: datetime, end_date: datetime, files: List[str], ai_committer: str
) -> Dict[str, Dict[str, int]]:
    """Get line counts per author for each file."""
    file_counts = {}

    for file in tqdm(files, desc="Analyzing files"):
        try:
            blame_output = run_git_command(
                [
                    "git",
                    "blame",
                    "-w",  # Ignore whitespace
                    "-M",  # Detect moved lines
                    "-C",  # Detect copied lines
                    f"--since={start_date.isoformat()}",
                    f"--until={end_date.isoformat()}",
                    "--line-porcelain",
                    "HEAD",
                    "--",
                    file,
                ]
            )

            counts = defaultdict(int)
            current_author = None

            for line in blame_output.split("\n"):
                if line.startswith("author-mail "):
                    author_mail = line[12:]
                    if author_mail == f"<{ai_committer.split('<')[1]}":
                        current_author = f"{current_author} (AI)"
                elif line.startswith("author "):
                    current_author = line[7:]
                elif line and not line.startswith("\t"):
                    if current_author:
                        counts[current_author] += 1

            if counts:
                file_counts[file] = dict(counts)

        except subprocess.CalledProcessError:
            continue

    return file_counts


def aggregate_by_period(
    data: Dict[str, Dict[str, int]], period: str
) -> List[Dict[str, Any]]:
    """Aggregate data by day, week, or month."""
    # Implementation would go here
    # For now, returning daily data
    return [{"date": datetime.now().strftime("%Y-%m-%d"), "data": data}]


@app.command()
def analyze(
    repo_path: Path = typer.Option(".", help="Path to git repository to analyze"),
    start_date: datetime = typer.Option(
        ..., formats=["%Y-%m-%d"], help="Start date for analysis (YYYY-MM-DD)"
    ),
    end_date: Optional[datetime] = typer.Option(
        None,
        formats=["%Y-%m-%d"],
        help="End date for analysis (YYYY-MM-DD), defaults to current date",
    ),
    ai_committer: str = typer.Option(
        DEFAULT_AI_COMMITTER,
        help="Committer name/email that identifies AI contributions",
    ),
    group_by: str = typer.Option("day", help="Group results by day, week, or month"),
    output: Optional[Path] = typer.Option(None, help="Output YAML file path"),
):
    """Analyze Git repository for AI vs. human code contributions."""

    # Change to repo directory
    original_dir = Path.cwd()
    try:
        os.chdir(repo_path)
    except (FileNotFoundError, NotADirectoryError):
        console.print(f"[red]Error: Repository path {repo_path} not found[/red]")
        raise typer.Exit(1)

    if not Path(".git").is_dir():
        console.print(f"[red]Error: {repo_path} is not a git repository[/red]")
        raise typer.Exit(1)

    if not end_date:
        end_date = datetime.now()

    if group_by not in ("day", "week", "month"):
        console.print("[red]Error: group-by must be 'day', 'week', or 'month'[/red]")
        raise typer.Exit(1)

    # Get all tracked files
    files = run_git_command(["git", "ls-tree", "-r", "--name-only", "HEAD"]).split("\n")

    # Filter files based on patterns
    files = [
        f
        for f in files
        if any(f.endswith(ext.replace("*", "")) for ext in DEFAULT_INCLUDE_PATTERNS)
        and not any(
            f.startswith(exc.replace("*", "")) for exc in DEFAULT_EXCLUDE_PATTERNS
        )
    ]

    # Get contribution counts
    file_counts = get_file_counts(start_date, end_date, files, ai_committer)

    # Calculate totals
    grand_total = defaultdict(int)
    ai_total = 0
    total_lines = 0

    for file_data in file_counts.values():
        for author, count in file_data.items():
            grand_total[author] += count
            total_lines += count
            if "(AI)" in author:
                ai_total += count

    ai_percentage = (ai_total / total_lines * 100) if total_lines > 0 else 0

    # Prepare output data
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "file_counts": file_counts,
        "grand_total": dict(
            sorted(grand_total.items(), key=itemgetter(1), reverse=True)
        ),
        "total_lines": total_lines,
        "ai_total": ai_total,
        "ai_percentage": round(ai_percentage, 2),
        "ai_commit_metadata": {"time_prompting": {"S": 0, "M": 0, "L": 0, "XL": 0}},
    }

    # Output results
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            yaml.dump(result, f, sort_keys=True)
    else:
        console.print(yaml.dump(result, sort_keys=True))

    # Display summary
    console.print(f"\nAI wrote {round(ai_percentage)}% of the code in this period.")

    try:
        # ... existing analysis code ...

        # Display summary
        console.print(f"\nAI wrote {round(ai_percentage)}% of the code in this period.")
    finally:
        # Return to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    app()
