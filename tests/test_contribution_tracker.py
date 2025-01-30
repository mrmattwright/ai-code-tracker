import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from pprint import pprint

import pytest
from ai_code_tracker.contribution_tracker import (
    aggregate_commits,
    app,
    parse_git_log,
)
from loguru import logger
from typer.testing import CliRunner


@pytest.fixture
def git_log_sample():
    sample_path = Path(__file__).parent / "fixtures" / "git_log_sample.txt"
    with open(sample_path) as f:
        return f.read()


@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository with some commits."""
    temp_dir = tempfile.mkdtemp()

    # Setup git repo
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    # Create and commit a test file
    test_file = os.path.join(temp_dir, "test.py")
    with open(test_file, "w") as f:
        f.write("print('hello')\n")

    subprocess.run(
        ["git", "add", "test.py"], cwd=temp_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        check=True,
        capture_output=True,
    )

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_parse_git_log_commit_count(git_log_sample):
    commits = parse_git_log(git_log_sample)
    logger.debug("first commit:")
    # pretty print the first commit
    pprint(commits[1])

    assert len(commits) == 7, "Should find exactly 7 commits in the sample"


def test_parse_git_log_time_prompting(git_log_sample):
    commits = parse_git_log(git_log_sample)

    # Check commit with time-prompting:S
    assert (
        commits[1]["time_prompting"] == "XL"
    ), "Second commit should have time_prompting 'XL'"

    # Check commit with time-prompting:M
    assert (
        commits[3]["time_prompting"] == "M"
    ), "Fourth commit should have time_prompting 'M'"

    # Check commit without time_prompting
    assert (
        commits[0].get("time_prompting") is None
    ), "First commit should not have time_prompting"


def test_aggregate_commits(git_log_sample):
    commits = parse_git_log(git_log_sample)
    df = aggregate_commits(commits, group_by="day")

    # Test basic structure
    assert len(df) > 0, "DataFrame should not be empty"
    assert "date" in df.columns, "DataFrame should have a date column"

    # Verify exact AI vs human commit counts
    assert df["ai_commits"].sum() == 2, "Should have exactly 2 AI commits"
    assert df["human_commits"].sum() == 5, "Should have exactly 5 human commits"

    # Verify AI changes (only counting .py, .js, .sh, Dockerfile, .md, and .yml files)
    # First AI commit: README.md (94+2) = 96
    # Second AI commit: git_contribution_analyzer.py (208) + stats.yaml (not counted) = 208
    ai_total = df["ai_total_changes"].sum()
    assert ai_total == 304, "AI should have made 304 total changes"

    # Human changes (only counting .py, .js, .sh, Dockerfile, .md, and .yml files)
    # First human: contribution_tracker.py (0) + git_log_sample.txt (not counted) = 0
    # Third human: git_contribution_analyzer.py (2) = 2
    # Fifth human: commit-msg-check.sh (23) + blame.py (308) = 331
    # Sixth human: __init__.py (2) = 2
    # Initial: README.md (2) = 2
    human_total = df["human_total_changes"].sum()
    assert human_total == 337, "Humans should have made 337 total changes"

    # Verify percentage calculation
    expected_ai_percentage = round((304 / (304 + 337)) * 100, 2)
    actual_percentage = df["percentage_total_changes_ai"].iloc[0]
    assert (
        actual_percentage == expected_ai_percentage
    ), f"AI percentage should be {expected_ai_percentage}%"

    # Verify time prompting counts
    assert df["time_prompting_XL"].sum() == 1, "Should have 1 small prompting session"
    assert df["time_prompting_M"].sum() == 1, "Should have 1 medium prompting session"
    assert df["time_prompting_L"].sum() == 0, "Should have 0 large prompting sessions"
    assert df["time_prompting_S"].sum() == 0, "Should have 0 small prompting sessions"


def test_repository_path(temp_git_repo):
    """Test that the repository path option works correctly."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--start-date",
            "2020-01-01",
            "--repository-path",
            temp_git_repo,
        ],
    )

    assert result.exit_code == 0, f"Command failed with output: {result.stdout}"

    # Verify the analysis results
    assert "'total_commits': 1" in result.stdout
    assert "'human_commits': 1" in result.stdout
    assert "'ai_commits': 0" in result.stdout  # Our test commit wasn't from AI
    assert "'human_lines_added': 1" in result.stdout  # We added one line in test.py
    assert "'human_lines_deleted': 0" in result.stdout  # We didn't delete any lines
