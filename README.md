# AI Code Tracker

Track and analyze the proportion of AI-assisted vs. human-written code in your Git repositories.

Heavily inspired by [Aider's Release History](https://aider.chat/HISTORY.html)

## Features

- Analyze Git repositories to determine AI vs. human code contributions
- Track contributions over time with daily, weekly, or monthly aggregation
- Generate detailed YAML reports with contribution statistics
- Smart file filtering for relevant source files
- Track AI commit metadata including time-prompting metrics

## Installation

```bash
# Clone the repository
git clone https://github.com/mrmattwright/ai-code-tracker
cd ai-code-tracker

# Install dependencies
uv sync
```

## Usage

```bash
# Basic usage
 uv run git_contribution_analyzer.py analyze --start-date 2024-01-01

# Save analysis to YAML file
 uv run git_contribution_analyzer.py analyze \
    --start-date 2024-01-01 \
    --output stats.yaml

# analysis of another repo
uv run git_contribution_analyzer.py analyze --start-date 2024-01-01 --repo-path /Users/matt/src/another-repo
```

### Options

- `--repo-path`: Path to Git repository (default: current directory)
- `--start-date`: Start date for analysis (YYYY-MM-DD) [required]
- `--end-date`: End date for analysis (YYYY-MM-DD) [default: current date]
- `--ai-committer`: Committer identifier for AI contributions [default: "llm <llm@opioinc.com>"]
- `--output`: Output YAML file path [optional]

### Output Format

The tool generates a YAML report with the following structure:

```yaml
date: YYYY-MM-DD
file_counts:
  "path/to/file.py":
    "Author Name": 120
    "AI": 45
grand_total:
  "Author Name": 500
  "AI": 150
total_lines: 650
ai_total: 150
ai_percentage: 23.08
ai_commit_metadata:
  time_prompting:
    S: 10
    M: 25
    L: 5
    XL: 2
```

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
