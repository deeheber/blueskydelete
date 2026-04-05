"""Bluesky Content Cleanup Tool

A Python script that automatically deletes old posts, reposts, and likes from Bluesky
based on a configurable age threshold. Designed to help keep your feed fresh by
cleaning up content older than a specified number of days.

Features:
- Colored logging with configurable levels
- Dry run mode for safe testing
- Flexible date range configuration
- Handles multiple content types (posts, reposts, likes)
- Proper error handling and input validation

Environment Variables:
- USERNAME: Bluesky username/handle (required)
- PASSWORD: Bluesky app password (required)
- DRY_RUN: 'true' for testing, 'false' for actual deletion (default: 'true')
- DAYS_AGO: Number of days back to delete content (default: 90)
- LOG_LEVEL: Logging level - DEBUG, INFO, WARNING, ERROR (default: 'INFO')

Usage:
    python main.py

Author: Danielle Heberling
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import requests

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DAYS_AGO = 90
DEFAULT_DRY_RUN = "true"
BATCH_SIZE = 100
COLLECTION_PREFIX = "app.bsky.feed."
LOG_SEPARATOR = "=" * 75
BSKY_ENTRYWAY = "https://bsky.social"

if not os.getenv("CI"):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print(
            "⚠️ Warning: python-dotenv not installed. Install with 'pip install -e .[dev]' for .env file support"
        )
        pass


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that adds colors to log levels for better readability."""

    COLORS = {
        "DEBUG": "\033[38;5;208m",  # Orange
        "INFO": "\033[36m",  # Cyan
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes for the log level.

        Args:
            record: The log record to format

        Returns:
            Formatted log message with color codes
        """
        log_color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{log_color}[{record.levelname}]{self.RESET}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Set up color logging with configurable level.

    Returns:
        Configured logger instance
    """
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter("%(levelname)s %(message)s"))
    logger.addHandler(console_handler)

    logger.propagate = False

    logger.info(f"ℹ️ Log level set to {log_level}")
    return logger


def validate_environment() -> None:
    """Validate required environment variables are present and valid.

    Raises:
        SystemExit: If required variables are missing or invalid
    """
    required_vars = ["USERNAME", "PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"❌ Missing required environment variables: {', '.join(missing_vars)}"
        )
        raise SystemExit(1)

    days_ago_str = os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO))
    try:
        days_ago = int(days_ago_str)
        if days_ago < 0:
            print("❌ DAYS_AGO must be a non-negative integer")
            raise SystemExit(1)
    except ValueError:
        print(f"❌ DAYS_AGO must be a valid integer, got: {days_ago_str}")
        raise SystemExit(1) from None


def authenticate_client(
    logger: logging.Logger,
) -> tuple[dict[str, Any], str]:
    """Authenticate with Bluesky and return session and repo.

    Args:
        logger: Logger instance for output

    Returns:
        Tuple of (session_dict, repo_name)

    Raises:
        SystemExit: If authentication fails
    """
    repo = os.getenv("USERNAME", "")
    password = os.getenv("PASSWORD", "")

    logger.info("⏳ Logging in...")

    try:
        resp = requests.post(
            f"{BSKY_ENTRYWAY}/xrpc/com.atproto.server.createSession",
            json={"identifier": repo, "password": password},
        )
        resp.raise_for_status()
        logger.info("😎 Login successful!")
        return resp.json(), repo
    except requests.HTTPError as e:
        logger.error(f"Failed to login: {e}")
        raise SystemExit(1) from e


def fetch_and_process(
    collection_name: str,
    session: dict[str, Any],
    repo: str,
    logger: logging.Logger,
) -> None:
    """Fetch and process items from a collection for deletion.

    Args:
        collection_name: Type of collection ('post', 'repost',
            'like')
        session: Authenticated session dict with accessJwt and
            did
        repo: Repository/username to process
        logger: Logger instance for output

    Raises:
        SystemExit: If fetching records fails
    """
    collection_url = COLLECTION_PREFIX + collection_name

    access_token = session["accessJwt"]
    did = session["did"]
    headers = {"Authorization": f"Bearer {access_token}"}

    logger.info(f"🏁 Starting to process {collection_name}s")
    try:
        items: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {
                "repo": did,
                "collection": collection_url,
                "limit": BATCH_SIZE,
                "reverse": True,
            }
            if cursor:
                params["cursor"] = cursor

            resp = requests.get(
                f"{BSKY_ENTRYWAY}/xrpc/" "com.atproto.repo.listRecords",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            items.extend(data["records"])

            if not data.get("cursor"):
                break
            cursor = data["cursor"]

        logger.info(f"⭐️ Fetched {len(items)} {collection_name}s total")
    except requests.HTTPError as e:
        logger.error(f"Failed to get {collection_name}s: {e}")
        raise SystemExit(1) from e

    try:
        num_days = int(os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO)))
    except ValueError:
        logger.error("DAYS_AGO must be a valid integer")
        raise SystemExit(1) from None

    target_date = datetime.now() - timedelta(days=num_days)
    logger.info(
        f"🗓️ Target date: {target_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
    )

    num_deleted = 0
    dry_run = os.getenv("DRY_RUN", DEFAULT_DRY_RUN).lower() == "true"

    for item in items:
        # Break early to save cycles if current post
        # is after target date
        if (
            datetime.strptime(
                item["value"]["createdAt"],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            )
            > target_date
        ):
            break

        item_timestamp = datetime.strptime(
            item["value"]["createdAt"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )

        if not dry_run:
            try:
                logger.info(
                    f"⏳ Deleting {collection_name} from "
                    f"{item_timestamp.strftime('%Y-%m-%d %H:%M:%S')}..."
                )
                logger.info(f"🔗 URI: {item['uri']}")

                logger.debug(
                    f"📋 Item details:\n" f"{json.dumps(item, indent=2)}"
                )

                # Extract rkey from the AT URI
                # URI format: at://did:plc:xxx/collection/rkey
                rkey = item["uri"].rsplit("/", 1)[-1]

                resp = requests.post(
                    f"{BSKY_ENTRYWAY}/xrpc/" "com.atproto.repo.deleteRecord",
                    json={
                        "repo": did,
                        "collection": collection_url,
                        "rkey": rkey,
                    },
                    headers=headers,
                )
                resp.raise_for_status()
                logger.info(
                    f"🎉 {collection_name.title()} deleted" " successfully! ✅"
                )

                logger.info(LOG_SEPARATOR)
                num_deleted += 1

            except requests.HTTPError as e:
                logger.error(
                    f"❌ Failed to delete {collection_name}"
                    f" {item['uri']}: {e}"
                )
                logger.error(f"💥 HTTPError details: {e!s}")
                logger.info(LOG_SEPARATOR)
                # Continue processing other items
                continue
            except Exception as e:
                logger.error(
                    f"💀 Unexpected error deleting"
                    f" {collection_name} {item['uri']}: {e}"
                )
                logger.info(LOG_SEPARATOR)
                continue
        else:
            logger.warning(
                f"🔄 DRY RUN: Would delete {collection_name}"
                f" from"
                f" {item_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            logger.warning(f"🔗 URI: {item['uri']}")
            logger.warning(f"📅 Created: {item['value']['createdAt']}")

            logger.debug(
                f"📋 Item details (dry run):\n" f"{json.dumps(item, indent=2)}"
            )

            logger.info(LOG_SEPARATOR)
            num_deleted += 1

    logger.info(
        f"✅ {num_deleted} {collection_name}s"
        f" {'deleted' if not dry_run else 'processed'}!"
    )
    logger.info(f"🚀 All done with {collection_name}s")
    logger.info(LOG_SEPARATOR)


def main() -> None:
    """Main function to orchestrate the Bluesky cleanup.

    Validates environment, sets up logging, authenticates
    with Bluesky, and processes posts, reposts, and likes
    for deletion based on age.
    """
    validate_environment()
    logger = setup_logging()
    session, repo = authenticate_client(logger)

    fetch_and_process("post", session, repo, logger)
    fetch_and_process("repost", session, repo, logger)
    fetch_and_process("like", session, repo, logger)

    logger.info("✨ All done!")


if __name__ == "__main__":
    main()
