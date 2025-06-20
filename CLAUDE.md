# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Commands
- `uv sync` - Install dependencies (uses uv as package manager)
- `uv run arxiv-notifier --help` - Show all available commands
- `uv run arxiv-notifier config` - Show current configuration
- `uv run arxiv-notifier test` - Test all connections (arXiv, Slack, Notion)
- `uv run arxiv-notifier once` - Run once manually
- `uv run arxiv-notifier run` - Start scheduler for continuous operation

### Testing Commands
- `uv run pytest` - Run all tests
- `uv run pytest --cov=src/arxiv_notifier --cov-report=html` - Run tests with coverage
- `uv run pytest tests/arxiv_notifier/test_models.py` - Run specific test file

### Code Quality Commands
- `uv run ruff check .` - Check code formatting and linting
- `uv run ruff check --fix .` - Auto-fix formatting issues
- `uv run mypy src/` - Run type checking

### Database Commands
- `uv run arxiv-notifier db stats` - Show database statistics
- `uv run arxiv-notifier db cleanup` - Clean up old records
- `uv run arxiv-notifier db reset` - Reset database (destructive)

## Architecture Overview

This is an arXiv paper monitoring and notification system with two main entry points:

1. **Main Application (`src/arxiv_notifier/`)**: Complete arXiv paper notification system
   - Fetches papers from arXiv API based on keywords/categories
   - Posts to Slack channels via webhooks
   - Saves to Notion databases
   - Tracks processed papers in SQLite to prevent duplicates
   - Supports both scheduled and one-time execution

2. **Core Framework (`src/core/`)**: Generic application framework (appears to be boilerplate)

### Key Components

- **`arxiv_client.py`**: arXiv API interaction with rate limiting
- **`slack_client.py`**: Slack webhook posting
- **`notion_client.py`**: Notion database integration
- **`processor.py`**: Main processing logic that coordinates all components
- **`scheduler.py`**: Handles both time-based and interval-based scheduling
- **`database.py`**: SQLite management for duplicate prevention
- **`models.py`**: Pydantic models for Paper and ProcessedPaper
- **`config.py`**: Environment-based configuration using pydantic-settings
- **`project_relevance.py`**: AI-powered project relevance evaluation using OpenAI

### Configuration

The system uses environment variables (`.env` file) for configuration:
- `ARXIV_KEYWORDS`, `ARXIV_CATEGORIES` - What to search for
- `SLACK_WEBHOOK_URL` - Where to post notifications
- `NOTION_API_KEY`, `NOTION_DATABASE_ID` - Notion integration
- `OPENAI_API_KEY` - Optional Japanese summary generation
- `PROJECT_OVERVIEW_FILE`, `ENABLE_PROJECT_RELEVANCE` - Project relevance evaluation
- `SCHEDULE_TIME` or `SCHEDULE_INTERVAL_HOURS` - When to run

Generate sample config: `uv run arxiv-notifier generate-env`

### External Scheduler Support

The system supports external schedulers (crontab, GitHub Actions) using:
- `uv run arxiv-notifier once` - Single execution
- `scripts/run-once.sh` - Wrapper script with error handling

### Keyword Operator Support

The system supports AND/OR operators in keywords:
- `"machine learning" AND "deep learning"` - Both terms required
- `"NLP" OR "natural language processing"` - Either term
- Keywords are comma-separated for OR logic between different keyword groups

### Project Relevance Evaluation

New feature that analyzes how papers can be applied to specific projects:
- Requires a project overview markdown file describing the project's goals and technical areas
- Uses OpenAI API to generate application-specific comments for relevant papers
- Comments appear in both Slack notifications and Notion database entries
- Only papers with high relevance get comments; low-relevance papers are skipped
- Set `ENABLE_PROJECT_RELEVANCE=true` and `PROJECT_OVERVIEW_FILE=path/to/overview.md`

## Development Notes

- Uses `uv` as the package manager (not pip/poetry)
- Python 3.11+ required
- Uses loguru for logging with automatic rotation
- Pydantic for data validation and settings
- SQLAlchemy for database operations
- Click for CLI interface
- All external API calls have retry logic with exponential backoff
- Test files follow pytest conventions with fixtures
- Ruff is configured for comprehensive linting (ALL rules enabled with specific ignores)