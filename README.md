# blueskydelete

Recreating some of the functionality of https://tweetdelete.net/, but for bluesky.

Currently the script searches for posts (including replies), reposts, and likes of the currently logged in user from the beginning up until a configurable number of days ago and deletes them.

The goal is to only have posts and reposts that are at most a certain age (configurable via env vars, defaults to 90 days).

## Features

- **Colored logging** - Color-coded log levels for better output readability
- **Configurable log levels** - Set `LOG_LEVEL` to control verbosity (DEBUG, INFO, WARNING, ERROR)
- **Dry run mode** - Safe testing without actually deleting content
- **Flexible date ranges** - Configure how far back to delete with `DAYS_AGO`
- **Multiple content types** - Handles posts, reposts, and likes

## Quick Start (instructions are for on a Mac)

1. Clone this repo
2. Check the `.python-version` file for the version of python to use. Other versions might work, but this is the version used during creation.
3. Create a virtual environment: `python3 -m venv .venv`
4. Activate the virtual environment: `source .venv/bin/activate`
5. Install dependencies: `pip install -e .'[dev]'` (for development with dotenv support) or `pip install -e .` (for production)
6. Get env vars set up: `touch .env & cp .env.sample .env` and change the values in the created `.env`
7. Run script: `python main.py`

## Environment Variables

- `USERNAME` - Your Bluesky username/handle
- `PASSWORD` - Your Bluesky app password (not your main password)
- `DRY_RUN` - Set to `false` to actually delete content, `true` (default) for dry run mode
- `DAYS_AGO` - Number of days back to delete content (default: 90)
- `LOG_LEVEL` - Logging verbosity: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`

## Usage Examples

```bash
# Normal run (dry run mode, INFO logging)
python main.py

# Actually delete content with debug logging
LOG_LEVEL=DEBUG DRY_RUN=false python main.py

# Delete content older than 30 days
DAYS_AGO=30 DRY_RUN=false python main.py

# Quiet mode - only show warnings and errors
LOG_LEVEL=WARNING python main.py
```

## Safety Features

- **Dry run by default** - Script runs in safe mode unless explicitly disabled
- **Colored warnings** - Dry run operations show in yellow to make it clear no actual deletion is happening
- **Detailed logging** - Use `LOG_LEVEL=DEBUG` to see exactly what would be deleted before running for real

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

Common cron patterns:

- `0 0 * * 0` - Weekly on Sunday at midnight
- `0 12 1 * *` - Monthly on the 1st at noon
- `0 6 * * 1,3,5` - Monday, Wednesday, Friday at 6 AM

**Note**: The workflow uses colored logging output which displays nicely in GitHub Actions logs, making it seamless to monitor the cleanup process.
