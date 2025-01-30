#!/usr/bin/env python3

import subprocess
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import typer
from loguru import logger
from rich.console import Console

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

app = typer.Typer(help="Track AI vs Human contributions over time")
console = Console()


def parse_git_log(log_output: str) -> List[Dict]:
    """Parse git log output into structured data."""
    commits = []
    current_commit = None

    # Split by commit delimiter and filter empty entries
    commit_blocks = [
        block.strip() for block in log_output.split("===COMMIT===") if block.strip()
    ]

    for block in commit_blocks:
        lines = block.split("\n")
        header = lines[0].split(",")

        if len(header) >= 4:  # Valid commit header
            hash, date, author, *msg_parts = header
            message = ",".join(msg_parts)

            current_commit = {
                "hash": hash,
                "date": date,
                "author": author,
                "message": message.strip(),
                "files": [],
                "time_prompting": None,
            }

            # Process remaining lines for time-prompting and file stats
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                if "time-prompting:" in line:
                    current_commit["time_prompting"] = line.split("time-prompting:")[
                        1
                    ].strip()
                elif line[0].isdigit() or line[0] == "-":  # File stats line
                    parts = line.split("\t")
                    if len(parts) == 3:
                        additions = int(parts[0]) if parts[0] != "-" else 0
                        deletions = int(parts[1]) if parts[1] != "-" else 0
                        filename = parts[2]

                        if any(
                            filename.endswith(pat.replace("*", ""))
                            for pat in DEFAULT_INCLUDE_PATTERNS
                        ) and not any(
                            filename.startswith(pat.replace("*", ""))
                            for pat in DEFAULT_EXCLUDE_PATTERNS
                        ):
                            current_commit["files"].append(
                                {
                                    "filename": filename,
                                    "additions": additions,
                                    "deletions": deletions,
                                }
                            )

            commits.append(current_commit)

    return commits


def aggregate_commits(commits: List[Dict], group_by: str = "day") -> pd.DataFrame:
    """Aggregate commit data into a DataFrame."""
    records = []

    # Group commits by date
    date_groups = {}
    for commit in commits:
        date = commit["date"]
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(commit)

    for date, date_commits in date_groups.items():
        ai_commits = sum(
            1
            for c in date_commits
            if c["author"] == DEFAULT_AI_COMMITTER.split("<")[0].strip()
        )
        total_commits = len(date_commits)
        human_commits = total_commits - ai_commits

        ai_lines_added = 0
        ai_lines_deleted = 0
        human_lines_added = 0
        human_lines_deleted = 0

        time_prompting = {"S": 0, "M": 0, "L": 0, "XL": 0}

        for commit in date_commits:
            is_ai = commit["author"] == DEFAULT_AI_COMMITTER.split("<")[0].strip()

            if commit["time_prompting"]:
                time_prompting[commit["time_prompting"]] += 1

            for file in commit["files"]:
                if is_ai:
                    ai_lines_added += file["additions"]
                    ai_lines_deleted += file["deletions"]
                else:
                    human_lines_added += file["additions"]
                    human_lines_deleted += file["deletions"]

        ai_total_changes = ai_lines_added + ai_lines_deleted
        human_total_changes = human_lines_added + human_lines_deleted
        total_changes = ai_total_changes + human_total_changes
        percentage_total_changes_ai = (
            (ai_total_changes / total_changes * 100) if total_changes > 0 else 0
        )

        records.append(
            {
                "date": date,
                "ai_commits": ai_commits,
                "total_commits": total_commits,
                "human_commits": human_commits,
                "ai_lines_added": ai_lines_added,
                "ai_lines_deleted": ai_lines_deleted,
                "ai_total_changes": ai_total_changes,
                "human_lines_added": human_lines_added,
                "human_lines_deleted": human_lines_deleted,
                "human_total_changes": human_total_changes,
                "percentage_total_changes_ai": round(percentage_total_changes_ai, 2),
                "time_prompting_S": time_prompting["S"],
                "time_prompting_M": time_prompting["M"],
                "time_prompting_L": time_prompting["L"],
                "time_prompting_XL": time_prompting["XL"],
            }
        )

    df = pd.DataFrame(records)

    if group_by == "week":
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").resample("W").sum().reset_index()

    return df


@app.command()
def analyze(
    start_date: datetime = typer.Option(
        ..., formats=["%Y-%m-%d"], help="Start date for analysis (YYYY-MM-DD)"
    ),
    end_date: Optional[datetime] = typer.Option(
        None, formats=["%Y-%m-%d"], help="End date for analysis (YYYY-MM-DD)"
    ),
    group_by: str = typer.Option("day", help="Group results by 'day' or 'week'"),
    repository_path: Optional[str] = typer.Option(
        None, help="Full local path to Git repository (defaults to current directory)"
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
            "-C",
            repository_path if repository_path else ".",
            "log",
            f"--since={start_date.isoformat()}",
            f"--until={end_date.isoformat()}",
            '--pretty="===COMMIT===%n%H,%ad,%an,%B"',
            "--date=short",
            "--numstat",
        ]
        logger.info(f"Running git log command: {' '.join(cmd)}")

        git_log = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        commits = parse_git_log(git_log)

        logger.info(f"Found {len(commits)} commits")

        df = aggregate_commits(commits, group_by)

        # Display results
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        # Convert DataFrame to a Rich table
        table = df.reset_index().to_dict("records")
        console.print("\n[bold]Contribution Analysis[/bold]")
        console.print(table, justify="left")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running git command: {e.stderr}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
