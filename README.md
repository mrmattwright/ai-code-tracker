# AI Code Tracker

Track and analyze the proportion of AI-assisted vs. human-written code in your Git repositories.

Heavily inspired by [Aider's Release History](https://aider.chat/HISTORY.html)

[![AI Code Percentage](charts/static/ai_code_percentage.png)](charts/ai_code_percentage.html)
[![Lines of Code](charts/static/lines_of_code.png)](charts/lines_of_code.html)
[![Time Prompting](charts/static/time_prompting.png)](charts/time_prompting.html)

## Features

- Analyze Git repositories to determine AI vs. human code contributions
- Track contributions over time with daily or weekly aggregation
- Smart file filtering for relevant source files
- Track AI commit metadata including time-prompting metrics (S/M/L/XL)
- Detailed statistics including lines added/deleted and percentage of AI changes
- Generate interactive visualizations:
  - AI Code Percentage by Day
  - New Lines of Code by Day (AI vs. Human)
  - Time Prompting Breakdown by Day

## Installation

```bash
# Clone the repository
git clone https://github.com/mrmattwright/ai-code-tracker
cd ai-code-tracker

# Install dependencies
uv sync
```

## Docker Usage

You can either build the image locally or use the pre-built image from Docker Hub:

```bash
# Using pre-built image
docker run -v $(pwd):/app mrmattwright/ai-code-tracker --start-date 2025-01-01

# Or build locally
docker build -t ai-code-tracker .

# Run with basic options (using local build)
docker run -v $(pwd):/app ai-code-tracker --start-date 2025-01-01

# Run with all options
docker run -v $(pwd):/app ai-code-tracker \
  --start-date 2025-01-01 \
  --end-date 2025-03-01 \
  --group-by week \
  --output-dir ./charts

# Run tests in container
docker run ai-code-tracker pytest
```

## Git Configuration

To track AI vs human contributions, you need to set up your Git configuration to use different author information when committing AI-generated code. The tool identifies AI contributions by matching the author email in `DEFAULT_AI_COMMITTER` (default: "llm <llm@opioinc.com>").

### Setting Up Multiple Git Configs

Create a `.gitconfig` for your AI commits:

```ini
[user]
    name = llm
    email = llm@opioinc.com
```

And one for your human commits:

```ini
[user]
    name = Your Name
    email = your.email@example.com
```

You can switch between configs using:

```bash
# For AI commits
git config --local include.path ../.gitconfig-ai

# For human commits
git config --local include.path ../.gitconfig-human
```

Or set per-command author:

```bash
# For one-off AI commits
git commit -m "AI generated change" --author="llm <llm@opioinc.com>"
```

## Configuring the AI Committer

You can configure the AI committer via the `AI_COMMITTER` environment variable. By default, it is set to `"llm <llm@opioinc.com>"`, but you can override this without modifying For example, if you're using [direnv](https://direnv.net/), add the following line to your `.envrc`:

```bash
export AI_COMMITTER="your_name <your_email@example.com>"
```


### Commit Message Format

When committing AI-generated code, you need to include a time-prompting metric in your commit message:

```bash
git commit -m "feat: Add new feature

time-prompting: M"
```

Valid time-prompting values are:
- `S`: Small (< 5 minutes)
- `M`: Medium (5-15 minutes)
- `L`: Large (15-30 minutes)
- `XL`: Extra Large (> 30 minutes)

### Enforcing Commit Message Format

You can enforce the time-prompting format for AI commits by adding a Git commit hook. Create `.git/hooks/commit-msg`:

```bash
#!/bin/bash

COMMIT_MSG_FILE="$1"
COMMITTER_EMAIL=$(git config --get user.email)
TARGET_EMAIL="llm@opioinc.com"

# Only enforce for AI commits
if [[ "$COMMITTER_EMAIL" == "$TARGET_EMAIL" ]]; then
    if ! grep -Eq "time-prompting:\s*(S|M|L|XL)\b" "$COMMIT_MSG_FILE"; then
        echo "ERROR: Commit message must include 'time-prompting: S|M|L|XL'"
        exit 1
    fi
fi

exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/commit-msg
```

## Usage

```bash
# Basic usage with date range
uv run contribution_tracker.py --start-date 2025-01-01 --end-date 2025-03-01

# Group by week instead of day
uv run contribution_tracker.py --start-date 2025-01-01 --group-by week

# Generate interactive charts
uv run contribution_tracker.py --start-date 2025-01-01 --output-dir ./charts

# Run tests
uv run pytest
```

### Options

- `--start-date`: Start date for analysis (YYYY-MM-DD) [required]
- `--end-date`: End date for analysis (YYYY-MM-DD) [default: current date]
- `--group-by`: Group results by 'day' or 'week' [default: day]
- `--output-dir`: Directory to save charts (enables chart generation) [optional]
- `--chart-format`: Chart output format (html, png, pdf) [default: html]

### Sample Output

```json
{
    "date": "2025-01-30",
    "ai_commits": 2,
    "total_commits": 7,
    "human_commits": 5,
    "ai_lines_added": 302,
    "ai_lines_deleted": 2,
    "ai_total_changes": 304,
    "human_lines_added": 337,
    "human_lines_deleted": 0,
    "human_total_changes": 337,
    "percentage_total_changes_ai": 47.43,
    "time_prompting_S": 1,
    "time_prompting_M": 1,
    "time_prompting_L": 0,
    "time_prompting_XL": 0
}
```

### Generated Charts

When using the `--output-dir` option, the tool generates three interactive charts:

1. **AI Code Percentage by Day**: Line chart showing the percentage of AI-written code over time
2. **New Lines of Code by Day**: Stacked bar chart comparing AI and human-added lines
3. **Time Prompting Breakdown**: Stacked bar chart showing the distribution of time-prompting categories (S/M/L/XL)

Charts are generated in HTML format by default for maximum interactivity. PNG and PDF formats are also supported if the `kaleido` package is installed.

## File Filtering

By default, the tool analyzes files with these extensions:
- `.js`
- `.py`
- `.scm`
- `.sh`
- `Dockerfile`
- `.md`
- `.github/workflows/*.yml`

Excluded patterns:
- `tests/fixtures/watch/*`
- `**/prompts.py`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
