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

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from atproto import Client, exceptions

# Constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DAYS_AGO = 90
DEFAULT_DRY_RUN = "true"
BATCH_SIZE = 100
COLLECTION_PREFIX = "app.bsky.feed."
LOG_SEPARATOR = "=" * 75

if os.getenv("CI"):
    print("Running in CI...skipping dotenv import.")
else:
    from dotenv import load_dotenv
    load_dotenv()

# Custom colored formatter
class ColoredFormatter(logging.Formatter):
    """Custom logging formatter that adds colors to log levels for better readability."""
    
    COLORS = {
        'DEBUG': '\033[38;5;208m',  # Orange
        'INFO': '\033[36m',         # Cyan
        'WARNING': '\033[33m',      # Yellow
        'ERROR': '\033[31m',        # Red
        'CRITICAL': '\033[35m',     # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes for the log level.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log message with color codes
        """
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}[{record.levelname}]{self.RESET}"
        return super().format(record)

def setup_logging() -> logging.Logger:
    """Set up colored logging with configurable level.
    
    Returns:
        Configured logger instance
    """
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level))

    # Create console handler with colored formatter including timestamps
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(console_handler)

    # Prevent duplicate logs
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
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        raise SystemExit(1)
    
    # Validate DAYS_AGO if provided
    days_ago_str = os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO))
    try:
        days_ago = int(days_ago_str)
        if days_ago < 0:
            print("❌ DAYS_AGO must be a non-negative integer")
            raise SystemExit(1)
    except ValueError:
        print(f"❌ DAYS_AGO must be a valid integer, got: {days_ago_str}")
        raise SystemExit(1)


def authenticate_client(logger: logging.Logger) -> tuple[Client, str]:
    """Authenticate with Bluesky and return client and repo.
    
    Args:
        logger: Logger instance for output
        
    Returns:
        Tuple of (authenticated_client, repo_name)
        
    Raises:
        SystemExit: If authentication fails
    """
    client = Client()
    repo = os.getenv("USERNAME", "")
    password = os.getenv("PASSWORD", "")

    logger.info("⏳ Logging in...")
    
    try:
        client.login(repo, password)
        logger.info("😎 Login successful!")
        return client, repo
    except exceptions.AtProtocolError as e:
        logger.error(f"Failed to login: {e}")
        raise SystemExit(1) from e

def fetch_and_process(collection_name: str, client: Client, repo: str, logger: logging.Logger) -> None:
    """Fetch and process items from a specific collection for deletion.
    
    Args:
        collection_name: Type of collection to process ('post', 'repost', 'like')
        client: Authenticated Bluesky client
        repo: Repository/username to process
        logger: Logger instance for output
        
    Raises:
        SystemExit: If fetching records fails
    """
    # Fetch items
    collection_url = COLLECTION_PREFIX + collection_name

    logger.info(f"🏁 Starting to process {collection_name}s")
    try:
        items = []
        cursor = None

        while True:
            result = client.com.atproto.repo.list_records(
                params={
                    "repo": repo,
                    "collection": collection_url,
                    "limit": BATCH_SIZE,
                    "cursor": cursor,
                    "reverse": True,
                }
            )

            items.extend(result.records)

            if not result.cursor:
                break
            cursor = result.cursor

        logger.info(f"⭐️ Fetched {len(items)} {collection_name}s total")
    except exceptions.AtProtocolError as e:
        logger.error(f"Failed to get {collection_name}s: {e}")
        raise SystemExit(1) from e

    try:
        num_days = int(os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO)))
    except ValueError:
        logger.error("DAYS_AGO must be a valid integer")
        raise SystemExit(1)
        
    target_date = datetime.now() - timedelta(days=num_days)
    logger.info(f"🗓️ Target date: {target_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}")

    client_method = f"delete_{collection_name}"
    num_deleted = 0
    dry_run = os.getenv("DRY_RUN", DEFAULT_DRY_RUN).lower() == "true"

    for item in items:
        # Break early to save some cycles if current post is after target date
        if datetime.strptime(item.value.created_at, "%Y-%m-%dT%H:%M:%S.%fZ") > target_date:
            break

        # Enhanced logging with timestamps and emojis for deletion operations
        item_timestamp = datetime.strptime(item.value.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        if not dry_run:
            try:
                logger.info(f"⏳ Deleting {collection_name} from {item_timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
                logger.info(f"🔗 URI: {item.uri}")
                
                # Debug logging for item details using model_dump_json with indentation
                logger.debug(f"📋 Item details:\n{item.model_dump_json(indent=2)}")
                
                # Perform deletion
                getattr(client, client_method)(item.uri)
                logger.info(f"🎉 {collection_name.title()} deleted successfully! ✅")
                
                # Only increment counter when deletion actually succeeds
                num_deleted += 1
                
            except exceptions.AtProtocolError as e:
                # Proper exception handling for AtProtocolError during deletions
                logger.error(f"❌ Failed to delete {collection_name} {item.uri}: {e}")
                logger.error(f"💥 AtProtocolError details: {str(e)}")
                # Continue processing other items even if one fails - do NOT increment counter
                continue
            except Exception as e:
                # Handle any other unexpected exceptions
                logger.error(f"💀 Unexpected error deleting {collection_name} {item.uri}: {e}")
                # Continue processing other items even if one fails - do NOT increment counter
                continue
        else:
            # Improved dry run logging with warnings and detailed item information
            logger.warning(f"🔄 DRY RUN: Would delete {collection_name} from {item_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.warning(f"🔗 URI: {item.uri}")
            logger.warning(f"📅 Created: {item.value.created_at}")
            
            # Debug logging for item details in dry run mode
            logger.debug(f"📋 Item details (dry run):\n{item.model_dump_json(indent=2)}")
            
            # Only increment counter for dry run items that would be processed
            num_deleted += 1

        # Addition of LOG_SEPARATOR for better log readability
        logger.info(LOG_SEPARATOR)

    logger.info(f"✅ {num_deleted} {collection_name}s {'deleted' if not dry_run else 'processed'}!")
    logger.info(f"🚀 All done with {collection_name}s")


def main() -> None:
    """Main function to orchestrate the Bluesky cleanup process.
    
    Validates environment, sets up logging, authenticates with Bluesky,
    and processes posts, reposts, and likes for deletion based on age.
    """
    validate_environment()
    logger = setup_logging()
    client, repo = authenticate_client(logger)
    
    fetch_and_process("post", client, repo, logger)
    fetch_and_process("repost", client, repo, logger)
    fetch_and_process("like", client, repo, logger)


if __name__ == "__main__":
    main()
