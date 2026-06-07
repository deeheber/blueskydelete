# 🧹 blueskydelete

Recreating some of the functionality of https://tweetdelete.net/, but for Bluesky!

Automatically cleans up your Bluesky posts, reposts, and likes older than a configurable number of days (default: 90 days).

## Quick Start

> This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).

1. **Clone this repo**
2. **Use Python 3.14** - see `.python-version` (the project requires `>=3.14,<3.15`)
3. **Install dependencies**: `uv sync`
4. **Setup environment**:
   - **macOS/Linux**: `cp .env.sample .env` then edit `.env` with your values
   - **Windows**: `copy .env.sample .env` then edit `.env` with your values
5. **Run script**: `uv run --env-file .env main.py` (or use the shortcut `./scripts/run.sh` from the repo root)

## Environment Variables

| Variable    | Description                                                 | Default |
| ----------- | ----------------------------------------------------------- | ------- |
| `USERNAME`  | Your Bluesky username/handle                                | -       |
| `PASSWORD`  | Your Bluesky app password (not main password!)              | -       |
| `DRY_RUN`   | Safe mode: `true` for testing, `false` for real deletion    | `true`  |
| `DAYS_AGO`  | How many days back to delete content                        | `90`    |
| `LOG_LEVEL` | Logging detail: `DEBUG`, `INFO`, `WARNING`, `ERROR`         | `INFO`  |

## Usage

Set your values in `.env` (see the table above), then run `./scripts/run.sh`
from the repo root (a shortcut for `uv run --env-file .env main.py`).

You can also override any variable inline, e.g.
`DRY_RUN=false DAYS_AGO=30 ./scripts/run.sh`.

## Safety Features

- **Dry run by default** - runs in safe mode unless `DRY_RUN=false`.
- **Colored logging** - dry-run operations print in yellow so it's clear nothing is being deleted. Set `LOG_LEVEL=DEBUG` to see exactly what would be deleted before a real run.

## Automated Scheduling

The repository includes a GitHub Actions workflow (`.github/workflows/cleanup-feed.yml`) that automatically runs the cleanup script on a schedule.

**Current schedule**: Every Friday at 5:00 AM UTC (`0 5 * * 5`)

### Setting up automated runs:

1. **Repository Variables** (Settings → Secrets and variables → Actions → Variables):

   - `USERNAME` - Your Bluesky username/handle
   - `DRY_RUN` - Set to `false` to actually delete, `true` for dry run
   - `DAYS_AGO` - Number of days back to delete (optional, defaults to 90)

2. **Repository Secrets** (Settings → Secrets and variables → Actions → Secrets):

   - `PASSWORD` - Your Bluesky app password

3. **Manual runs**: You can also trigger the workflow manually from the Actions tab

### Customizing the schedule:

Edit the cron expression in `.github/workflows/cleanup-feed.yml`:

```yaml
schedule:
  - cron: "0 5 * * 5" # Every Friday at 5 AM UTC
```

**Common cron patterns:**

- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 12 1 * *` - Monthly on the 1st at noon
- `0 6 * * 1,3,5` - Monday, Wednesday, Friday at 6 AM

## Development

### Code Quality

The project includes automated code quality checks using:

- **Black** - Code formatting
- **Ruff** - Fast Python linter with auto-fix
- **MyPy** - Static type checking

**Run checks locally:**

```bash
# Run all checks with auto-fix
./scripts/code-quality.sh

# Individual tools
uv run black .                    # Format code
uv run ruff check --fix .         # Lint with auto-fix
uv run mypy .                     # Type check
```

**CI:** Code quality checks run on pull requests and pushes to `main`; all must pass before merging.
