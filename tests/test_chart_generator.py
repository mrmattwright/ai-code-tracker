import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from ai_code_tracker.chart_generator import ChartGenerator
from ai_code_tracker.models import ChartConfig, ContributionStats


@pytest.fixture
def sample_stats():
    """Create sample contribution stats for testing."""
    return [
        ContributionStats(
            date=datetime(2024, 1, 1),
            ai_commits=2,
            total_commits=5,
            human_commits=3,
            ai_lines_added=100,
            ai_lines_deleted=20,
            ai_total_changes=120,
            human_lines_added=150,
            human_lines_deleted=30,
            human_total_changes=180,
            percentage_total_changes_ai=40.0,
            time_prompting_S=1,
            time_prompting_M=2,
            time_prompting_L=0,
            time_prompting_XL=1,
        ),
        ContributionStats(
            date=datetime(2024, 1, 2),
            ai_commits=3,
            total_commits=8,
            human_commits=5,
            ai_lines_added=200,
            ai_lines_deleted=40,
            ai_total_changes=240,
            human_lines_added=180,
            human_lines_deleted=20,
            human_total_changes=200,
            percentage_total_changes_ai=54.5,
            time_prompting_S=2,
            time_prompting_M=1,
            time_prompting_L=1,
            time_prompting_XL=0,
        ),
    ]


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for chart output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_chart_generator_initialization(temp_output_dir):
    """Test ChartGenerator initialization creates output directory."""
    config = ChartConfig(output_dir=temp_output_dir)
    ChartGenerator(config)
    assert Path(temp_output_dir).exists()


def test_generate_ai_percentage_chart(temp_output_dir, sample_stats):
    """Test generation of AI percentage chart."""
    config = ChartConfig(output_dir=temp_output_dir)
    generator = ChartGenerator(config)
    generator.generate_ai_percentage_chart(sample_stats)

    expected_file = Path(temp_output_dir) / "ai_code_percentage.html"
    assert expected_file.exists()
    assert expected_file.stat().st_size > 0


def test_generate_lines_of_code_chart(temp_output_dir, sample_stats):
    """Test generation of lines of code chart."""
    config = ChartConfig(output_dir=temp_output_dir)
    generator = ChartGenerator(config)
    generator.generate_lines_of_code_chart(sample_stats)

    expected_file = Path(temp_output_dir) / "lines_of_code.html"
    assert expected_file.exists()
    assert expected_file.stat().st_size > 0


def test_generate_time_prompting_chart(temp_output_dir, sample_stats):
    """Test generation of time prompting chart."""
    config = ChartConfig(output_dir=temp_output_dir)
    generator = ChartGenerator(config)
    generator.generate_time_prompting_chart(sample_stats)

    expected_file = Path(temp_output_dir) / "time_prompting.html"
    assert expected_file.exists()
    assert expected_file.stat().st_size > 0


def test_chart_format_png_fallback(temp_output_dir, sample_stats):
    """Test generation of charts with PNG format falls back to HTML when kaleido is not available."""
    config = ChartConfig(output_dir=temp_output_dir, format="png")
    generator = ChartGenerator(config)

    # Generate all charts
    generator.generate_ai_percentage_chart(sample_stats)
    generator.generate_lines_of_code_chart(sample_stats)
    generator.generate_time_prompting_chart(sample_stats)

    # Check all HTML files exist (fallback from PNG)
    assert (Path(temp_output_dir) / "ai_code_percentage.html").exists()
    assert (Path(temp_output_dir) / "lines_of_code.html").exists()
    assert (Path(temp_output_dir) / "time_prompting.html").exists()
