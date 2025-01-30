from pathlib import Path
from typing import List

import pandas as pd
import plotly.graph_objects as go
from loguru import logger

from .models import ChartConfig, ContributionStats


class ChartGenerator:
    def __init__(self, config: ChartConfig):
        self.config = config
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def _save_chart(self, fig: go.Figure, filename: str) -> None:
        """Save the chart in both HTML and PNG formats."""
        output_dir = Path(self.config.output_dir)
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)

        # Save HTML version
        html_path = output_dir / f"{filename}.html"
        fig.write_html(str(html_path))
        logger.info(f"Saved HTML chart to {html_path}")

        # Save PNG version
        try:
            png_path = static_dir / f"{filename}.png"
            # Set specific dimensions for badge-like appearance
            fig.update_layout(
                width=800,
                height=200,
                margin=dict(l=50, r=50, t=50, b=50),
            )
            fig.write_image(str(png_path))
            logger.info(f"Saved PNG chart to {png_path}")
        except ValueError as e:
            if "kaleido" in str(e):
                logger.warning(
                    f"PNG export not available. Please install kaleido: Error: {e}"
                )
            else:
                raise

    def generate_ai_percentage_chart(self, stats: List[ContributionStats]) -> None:
        """Generate bar chart showing AI code percentage over time."""
        df = pd.DataFrame([stat.model_dump() for stat in stats])

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["percentage_total_changes_ai"],
                name="AI Code Percentage",
            )
        )

        fig.update_layout(
            title="AI Code Percentage by Day",
            xaxis_title="Date",
            yaxis_title="Percentage of Changes (%)",
            yaxis_range=[0, 100],
        )

        self._save_chart(fig, "ai_code_percentage")

    def generate_lines_of_code_chart(self, stats: List[ContributionStats]) -> None:
        """Generate stacked bar chart showing lines of code added by AI vs humans."""
        df = pd.DataFrame([stat.model_dump() for stat in stats])

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["ai_lines_added"],
                name="AI Lines Added",
            )
        )
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["human_lines_added"],
                name="Human Lines Added",
            )
        )

        fig.update_layout(
            title="New Lines of Code by Day",
            xaxis_title="Date",
            yaxis_title="Lines Added",
            barmode="stack",
        )

        self._save_chart(fig, "lines_of_code")

    def generate_time_prompting_chart(self, stats: List[ContributionStats]) -> None:
        """Generate stacked bar chart showing time prompting distribution."""
        df = pd.DataFrame([stat.model_dump() for stat in stats])

        fig = go.Figure()
        for category in ["S", "M", "L", "XL"]:
            fig.add_trace(
                go.Bar(
                    x=df["date"],
                    y=df[f"time_prompting_{category}"],
                    name=f"Time Prompting {category}",
                )
            )

        fig.update_layout(
            title="Time Prompting Breakdown by Day",
            xaxis_title="Date",
            yaxis_title="Count",
            barmode="stack",
        )

        self._save_chart(fig, "time_prompting")
