#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from typing import List, Optional

import pandas as pd
import typer
from loguru import logger
from rich.console import Console

from .chart_generator import ChartGenerator
from .models import ChartConfig, Commit, CommitFile, ContributionStats

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

DEFAULT_AI_COMMITTER = os.environ.get("AI_COMMITTER", "llm <llm@opioinc.com>")

app = typer.Typer(help="Track AI vs Human contributions over time")
console = Console()


def parse_git_log(log_output: str) -> List[Commit]:
    """Parse git log output into structured data."""
    commits = []
    current_commit = None

    for commit_block in log_output.split("===COMMIT==="):
        if not commit_block.strip():
            continue

        lines = commit_block.strip().split("\n")
        header = lines[0]

        if "," not in header:
            continue

        hash, date, author, *msg_parts = header.split(",")
        message = ",".join(msg_parts)

        # Get full commit message including any additional lines before file stats
        full_message = message
        for line in lines[1:]:
            if line.strip() and not (
                line[0].isdigit() or line[0] == "-" or line.startswith('"')
            ):
                full_message += "\n" + line

        current_commit_files = []
        time_prompting = None

        # Extract time-prompting if present
        if "time-prompting:" in full_message:
            time_prompting = (
                full_message.split("time-prompting:")[1].strip().split("\n")[0]
            )

        # Process file changes
        for line in lines[1:]:
            if not line.strip():
                continue

            if line[0].isdigit() or line[0] == "-":  # File stats line
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    additions = int(parts[0]) if parts[0] != "-" else 0
                    deletions = int(parts[1]) if parts[1] != "-" else 0
                    filename = parts[2]

                    # Only include files matching patterns
                    if any(
                        filename.endswith(pat.replace("*", ""))
                        for pat in DEFAULT_INCLUDE_PATTERNS
                    ) and not any(
                        filename.startswith(pat.replace("*", ""))
                        for pat in DEFAULT_EXCLUDE_PATTERNS
                    ):
                        current_commit_files.append(
                            CommitFile(
                                filename=filename,
                                additions=additions,
                                deletions=deletions,
                            )
                        )

        commits.append(
            Commit(
                hash=hash,
                date=date,
                author=author,
                message=full_message.strip(),
                files=current_commit_files,
                time_prompting=time_prompting,
            )
        )

    return commits


def aggregate_commits(
    commits: List[Commit], group_by: str = "day"
) -> List[ContributionStats]:
    """Aggregate commit data into ContributionStats objects."""
    records = []

    # Group commits by date
    date_groups = {}
    for commit in commits:
        date = commit.date
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(commit)

    for date, date_commits in date_groups.items():
        ai_commits = sum(
            1
            for c in date_commits
            if c.author == DEFAULT_AI_COMMITTER.split("<")[0].strip()
        )
        total_commits = len(date_commits)
        human_commits = total_commits - ai_commits

        ai_lines_added = 0
        ai_lines_deleted = 0
        human_lines_added = 0
        human_lines_deleted = 0

        time_prompting = {"S": 0, "M": 0, "L": 0, "XL": 0}

        for commit in date_commits:
            is_ai = commit.author == DEFAULT_AI_COMMITTER.split("<")[0].strip()

            if commit.time_prompting:
                time_prompting[commit.time_prompting] += 1

            for file in commit.files:
                if is_ai:
                    ai_lines_added += file.additions
                    ai_lines_deleted += file.deletions
                else:
                    human_lines_added += file.additions
                    human_lines_deleted += file.deletions

        ai_total_changes = ai_lines_added + ai_lines_deleted
        human_total_changes = human_lines_added + human_lines_deleted
        total_changes = ai_total_changes + human_total_changes
        percentage_total_changes_ai = (
            (ai_total_changes / total_changes * 100) if total_changes > 0 else 0
        )

        stats = ContributionStats(
            date=datetime.strptime(date, "%Y-%m-%d"),
            ai_commits=ai_commits,
            total_commits=total_commits,
            human_commits=human_commits,
            ai_lines_added=ai_lines_added,
            ai_lines_deleted=ai_lines_deleted,
            ai_total_changes=ai_total_changes,
            human_lines_added=human_lines_added,
            human_lines_deleted=human_lines_deleted,
            human_total_changes=human_total_changes,
            percentage_total_changes_ai=round(percentage_total_changes_ai, 2),
            time_prompting_S=time_prompting["S"],
            time_prompting_M=time_prompting["M"],
            time_prompting_L=time_prompting["L"],
            time_prompting_XL=time_prompting["XL"],
        )
        records.append(stats)

    if group_by == "week":
        # Convert to DataFrame for weekly aggregation
        df = pd.DataFrame([stat.model_dump() for stat in records])
        df = df.set_index("date").resample("W").sum().reset_index()
        # Convert back to ContributionStats objects
        records = [ContributionStats(**record) for record in df.to_dict("records")]

    return records


@app.command()
def analyze(
    start_date: datetime = typer.Option(
        ..., formats=["%Y-%m-%d"], help="Start date for analysis (YYYY-MM-DD)"
    ),
    end_date: Optional[datetime] = typer.Option(
        None, formats=["%Y-%m-%d"], help="End date for analysis (YYYY-MM-DD)"
    ),
    group_by: str = typer.Option("day", help="Group results by 'day' or 'week'"),
    output_dir: Optional[str] = typer.Option(
        None, help="Directory to save charts (enables chart generation)"
    ),
    chart_format: str = typer.Option(
        "html", help="Chart output format (html, png, pdf)"
    ),
):
    """Analyze Git repository for AI vs. human code contributions over time."""
    if not end_date:
        end_date = datetime.now()

    if group_by not in ("day", "week"):
        console.print("[red]Error: group-by must be 'day' or 'week'[/red]")
        raise typer.Exit(1)

    try:
        cmd = [
            "git",
            "log",
            f"--since={start_date.isoformat()}",
            f"--until={end_date.isoformat()}",
            '--pretty="===COMMIT===%n%H,%ad,%an,%B"',
            "--date=short",
            "--numstat",
        ]
        logger.info(f"Running git command: {' '.join(cmd)}")

        git_log = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        commits = parse_git_log(git_log)
        logger.info(f"Found {len(commits)} commits")

        stats = aggregate_commits(commits, group_by)

        # Display results
        console.print("\n[bold]Contribution Analysis[/bold]")
        for stat in stats:
            console.print(stat.model_dump())

        # Generate charts if output directory is specified
        if output_dir:
            chart_config = ChartConfig(output_dir=output_dir, format=chart_format)
            chart_generator = ChartGenerator(chart_config)

            chart_generator.generate_ai_percentage_chart(stats)
            chart_generator.generate_lines_of_code_chart(stats)
            chart_generator.generate_time_prompting_chart(stats)

            console.print(f"\n[green]Charts generated in {output_dir}[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running git command: {e.stderr}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
