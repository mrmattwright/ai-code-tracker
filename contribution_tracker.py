#!/usr/bin/env python3

from datetime import datetime
from typing import Optional

import typer
from ai_code_tracker.contribution_tracker import analyze
from loguru import logger

app = typer.Typer(help="Track AI vs Human contributions over time")


@app.command()
def main(
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
    try:
        analyze(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            output_dir=output_dir,
            chart_format=chart_format,
        )
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
