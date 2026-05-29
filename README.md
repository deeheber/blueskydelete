# 🧹 blueskydelete

🔄 Recreating some of the functionality of https://tweetdelete.net/, but for Bluesky!

✨ **What it does**: Automatically cleans up your Bluesky posts, reposts, and likes older than a configurable number of days (default: 90 days).

🎯 **Goal**: Keep your feed fresh by only maintaining recent content while cleaning up the old stuff.

## ✨ Features

- 🎨 **Colored logging** - Color-coded log levels for better output readability
- 🔧 **Configurable log levels** - Set `LOG_LEVEL` to control verbosity (DEBUG, INFO, WARNING, ERROR)
- 🛡️ **Dry run mode** - Safe testing without actually deleting content
- 📅 **Flexible date ranges** - Configure how far back to delete with `DAYS_AGO`
- 📝 **Multiple content types** - Handles posts, reposts, and likes

## 🚀 Quick Start

> 💡 This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).

1. 📥 **Clone this repo**
2. 🐍 **Check Python version** - See `.python-version` file (other versions might work)
3. 📦 **Install dependencies**: `uv sync`
4. ⚙️ **Setup environment**:
   - **macOS/Linux**: `cp .env.sample .env` then edit `.env` with your values
   - **Windows**: `copy .env.sample .env` then edit `.env` with your values
5. 🎬 **Run script**: `uv run --env-file .env python main.py`

## ⚙️ Environment Variables

| Variable    | Description                                                 | Default |
| ----------- | ----------------------------------------------------------- | ------- |
| `USERNAME`  | 👤 Your Bluesky username/handle                             | -       |
| `PASSWORD`  | 🔐 Your Bluesky app password (not main password!)           | -       |
| `DRY_RUN`   | 🛡️ Safe mode: `true` for testing, `false` for real deletion | `true`  |
| `DAYS_AGO`  | 📅 How many days back to delete content                     | `90`    |
| `LOG_LEVEL` | 📊 Logging detail: `DEBUG`, `INFO`, `WARNING`, `ERROR`      | `INFO`  |

## 💡 Usage Examples

```bash
# Normal run (dry run mode, INFO logging)
uv run --env-file .env python main.py

# Actually delete content with debug logging
LOG_LEVEL=DEBUG DRY_RUN=false uv run --env-file .env python main.py

# Delete content older than 30 days
DAYS_AGO=30 DRY_RUN=false uv run --env-file .env python main.py

# Quiet mode - only show warnings and errors
LOG_LEVEL=WARNING uv run --env-file .env python main.py
```

> 📝 **Local vs CI**: Locally, `.env` is loaded via uv's `--env-file` flag. In GitHub Actions, environment variables come from repository secrets and variables directly — no `.env` file is used.

> 💡 **Tip**: To skip typing `--env-file .env` each time, run `export UV_ENV_FILE=.env` in your shell — uv will then load `.env` automatically, so a plain `uv run python main.py` works.

## 🛡️ Safety Features

- 🔒 **Dry run by default** - Script runs in safe mode unless explicitly disabled
- ⚠️ **Colored warnings** - Dry run operations show in yellow to make it clear no actual deletion is happening
- 🔍 **Detailed logging** - Use `LOG_LEVEL=DEBUG` to see exactly what would be deleted before running for real

## 🤖 Automated Scheduling

The repository includes a GitHub Actions workflow (`.github/workflows/cleanup-feed.yml`) that automatically runs the cleanup script on a schedule.

⏰ **Current schedule**: Every Friday at 5:00 AM UTC (`0 5 * * 5`)

### 🔧 Setting up automated runs:

1. **📊 Repository Variables** (Settings → Secrets and variables → Actions → Variables):

   - `USERNAME` - 👤 Your Bluesky username/handle
   - `DRY_RUN` - 🛡️ Set to `false` to actually delete, `true` for dry run
   - `DAYS_AGO` - 📅 Number of days back to delete (optional, defaults to 90)

2. **🔐 Repository Secrets** (Settings → Secrets and variables → Actions → Secrets):

   - `PASSWORD` - 🔑 Your Bluesky app password

3. **▶️ Manual runs**: You can also trigger the workflow manually from the Actions tab

### ⏰ Customizing the schedule:

Edit the cron expression in `.github/workflows/cleanup-feed.yml`:

```yaml
schedule:
  - cron: "0 5 * * 5" # Every Friday at 5 AM UTC
```

**📅 Common cron patterns:**

- `0 0 * * 0` - 🗓️ Weekly on Sunday at midnight
- `0 12 1 * *` - 📆 Monthly on the 1st at noon
- `0 6 * * 1,3,5` - 📋 Monday, Wednesday, Friday at 6 AM

💡 **Note**: The workflow uses colored logging output which displays nicely in GitHub Actions logs, making it seamless to monitor the cleanup process.

## 🔧 Development

### Code Quality

The project includes automated code quality checks using:

- **Black** - Code formatting
- **Ruff** - Fast Python linter with auto-fix
- **MyPy** - Static type checking

**Run checks locally:**

```bash
# Run all checks with auto-fix
./scripts/check-code.sh

# Individual tools
uv run black .                    # Format code
uv run ruff check --fix .         # Lint with auto-fix
uv run mypy .                     # Type check
```

**CI Integration:**

- Code quality checks run automatically on pull requests and main branch pushes
- All checks must pass before merging
- Uses the same tools as local development for consistency
