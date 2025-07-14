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

## 🚀 Quick Start (macOS)

1. 📥 **Clone this repo**
2. 🐍 **Check Python version** - See `.python-version` file (other versions might work)
3. 🏠 **Create virtual environment**: `python3 -m venv .venv`
4. ⚡ **Activate environment**: `source .venv/bin/activate`
5. 📦 **Install dependencies**:
   - Development: `pip install -e .'[dev]'`
   - Production: `pip install -e .`
6. ⚙️ **Setup environment**: `touch .env & cp .env.sample .env` then edit `.env` with your values
7. 🎬 **Run script**: `python main.py`

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
python main.py

# Actually delete content with debug logging
LOG_LEVEL=DEBUG DRY_RUN=false python main.py

# Delete content older than 30 days
DAYS_AGO=30 DRY_RUN=false python main.py

# Quiet mode - only show warnings and errors
LOG_LEVEL=WARNING python main.py
```

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
