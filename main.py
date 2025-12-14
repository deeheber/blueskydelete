"""Bluesky Content Cleanup Tool

A Python script that automatically deletes old posts, reposts, and likes from Bluesky
based on a configurable age threshold. Designed to help keep your feed fresh by
cleaning up content older than a specified number of days.

Features:
- Colored logging with configurable levels and timestamps
- Enhanced emoji-based status indicators for operations
- Dry run mode for safe testing with detailed simulation
- Flexible date range configuration
- Handles multiple content types (posts, reposts, likes)
- Robust error handling with retry mechanism for transient failures
- Comprehensive statistics tracking and progress reporting
- Graceful handling of network issues and API errors
- Batch processing with progress indicators for large datasets

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
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from atproto import Client, exceptions

# Constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DAYS_AGO = 90
DEFAULT_DRY_RUN = "true"
BATCH_SIZE = 100
COLLECTION_PREFIX = "app.bsky.feed."
LOG_SEPARATOR = "=" * 75
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

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


def delete_with_retry(client: Client, method_name: str, uri: str, logger: logging.Logger) -> bool:
    """Attempt to delete an item with retry mechanism for transient errors.
    
    Args:
        client: Authenticated Bluesky client
        method_name: Name of the deletion method to call
        uri: URI of the item to delete
        logger: Logger instance for output
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            getattr(client, method_name)(uri)
            return True
        except exceptions.AtProtocolError as e:
            error_msg = str(e).lower()
            
            # Check if this is a retryable error (network/server issues)
            retryable_errors = ['timeout', 'connection', 'server error', '5xx', 'temporarily']
            is_retryable = any(error_text in error_msg for error_text in retryable_errors)
            
            if attempt < MAX_RETRIES and is_retryable:
                logger.warning(f"⚠️ Attempt {attempt} failed with retryable error: {e}")
                logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
                continue
            else:
                # Non-retryable error or max retries exceeded
                logger.error(f"❌ Failed to delete after {attempt} attempts: {e}")
                logger.error(f"💥 AtProtocolError details: {str(e)}")
                return False
        except Exception as e:
            # Handle any other unexpected exceptions
            logger.error(f"💀 Unexpected error during deletion attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue
            return False
    
    return False


def format_deletion_statistics(stats: Dict[str, Any], collection_name: str, dry_run: bool) -> str:
    """Format detailed statistics for deletion operations.
    
    Args:
        stats: Dictionary containing deletion statistics
        collection_name: Type of collection processed
        dry_run: Whether this was a dry run
        
    Returns:
        Formatted statistics string
    """
    mode = "DRY RUN" if dry_run else "DELETION"
    total_processed = stats['successful'] + stats['failed'] + stats['skipped']
    
    stats_lines = [
        f"📊 {mode} STATISTICS FOR {collection_name.upper()}S:",
        f"   📈 Total items processed: {total_processed}",
        f"   ✅ Successful {'simulated ' if dry_run else ''}deletions: {stats['successful']}",
        f"   ❌ Failed deletions: {stats['failed']}",
        f"   ⏭️ Skipped (too new): {stats['skipped']}",
    ]
    
    if not dry_run and total_processed > 0:
        success_rate = (stats['successful'] / total_processed) * 100
        stats_lines.append(f"   🎯 Success rate: {success_rate:.1f}%")
    
    return "\n".join(stats_lines)


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
    # Initialize statistics tracking
    stats = {
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'total_fetched': 0
    }
    
    # Fetch items
    collection_url = COLLECTION_PREFIX + collection_name

    logger.info(f"🏁 Starting to process {collection_name}s")
    try:
        items = []
        cursor = None
        batch_count = 0

        while True:
            batch_count += 1
            logger.debug(f"🔄 Fetching batch {batch_count} (limit: {BATCH_SIZE})")
            
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
            logger.debug(f"📦 Batch {batch_count}: Retrieved {len(result.records)} items")

            if not result.cursor:
                break
            cursor = result.cursor

        stats['total_fetched'] = len(items)
        logger.info(f"⭐️ Fetched {len(items)} {collection_name}s total in {batch_count} batches")
        
    except exceptions.AtProtocolError as e:
        logger.error(f"❌ Failed to fetch {collection_name}s: {e}")
        logger.error(f"💥 AtProtocolError details: {str(e)}")
        raise SystemExit(1) from e
    except Exception as e:
        logger.error(f"💀 Unexpected error while fetching {collection_name}s: {e}")
        raise SystemExit(1) from e

    # Validate and parse DAYS_AGO
    try:
        num_days = int(os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO)))
    except ValueError:
        logger.error("❌ DAYS_AGO must be a valid integer")
        raise SystemExit(1)
        
    target_date = datetime.now() - timedelta(days=num_days)
    logger.info(f"🗓️ Target date: {target_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}")
    logger.info(f"📅 Will process items older than {num_days} days")

    client_method = f"delete_{collection_name}"
    dry_run = os.getenv("DRY_RUN", DEFAULT_DRY_RUN).lower() == "true"
    
    if dry_run:
        logger.warning("🔄 Running in DRY RUN mode - no actual deletions will be performed")
    else:
        logger.info("🚨 Running in LIVE mode - items will be permanently deleted")

    # Progress tracking
    eligible_items = []
    for item in items:
        item_date = datetime.strptime(item.value.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        if item_date <= target_date:
            eligible_items.append((item, item_date))
        else:
            stats['skipped'] += 1
            
    total_eligible = len(eligible_items)
    logger.info(f"🎯 Found {total_eligible} {collection_name}s eligible for deletion (skipping {stats['skipped']} newer items)")
    
    if total_eligible == 0:
        logger.info(f"✨ No {collection_name}s to process!")
        return

    # Process eligible items with progress logging
    for idx, (item, item_timestamp) in enumerate(eligible_items, 1):
        # Progress indicator for large batches
        if total_eligible > 10 and idx % max(1, total_eligible // 10) == 0:
            progress = (idx / total_eligible) * 100
            logger.info(f"📊 Progress: {progress:.0f}% ({idx}/{total_eligible}) {collection_name}s processed")

        # Enhanced logging with timestamps and emojis for deletion operations
        if not dry_run:
            try:
                logger.info(f"⏳ Deleting {collection_name} from {item_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({idx}/{total_eligible})...")
                logger.info(f"🔗 URI: {item.uri}")
                
                # Debug logging for item details using model_dump_json with indentation
                logger.debug(f"📋 Item details:\n{item.model_dump_json(indent=2)}")
                
                # Perform deletion with retry mechanism
                deletion_successful = delete_with_retry(client, client_method, item.uri, logger)
                
                if deletion_successful:
                    logger.info(f"🎉 {collection_name.title()} deleted successfully! ✅")
                    stats['successful'] += 1
                else:
                    logger.error(f"❌ Failed to delete {collection_name} {item.uri} after all retries")
                    stats['failed'] += 1
                    # Continue processing other items even if one fails
                    
            except Exception as e:
                # Catch-all for any other unexpected exceptions not handled by delete_with_retry
                logger.error(f"💀 Critical error processing {collection_name} {item.uri}: {e}")
                stats['failed'] += 1
                continue
        else:
            # Improved dry run logging with warnings and detailed item information
            logger.warning(f"🔄 DRY RUN: Would delete {collection_name} from {item_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({idx}/{total_eligible})")
            logger.warning(f"🔗 URI: {item.uri}")
            logger.warning(f"📅 Created: {item.value.created_at}")
            
            # Debug logging for item details in dry run mode
            logger.debug(f"📋 Item details (dry run):\n{item.model_dump_json(indent=2)}")
            
            # Count as successful for dry run statistics
            stats['successful'] += 1

        # Addition of LOG_SEPARATOR for better log readability (but only for debug level to reduce noise)
        logger.debug(LOG_SEPARATOR)

    # Final statistics and summary
    logger.info(LOG_SEPARATOR)
    logger.info(format_deletion_statistics(stats, collection_name, dry_run))
    logger.info(LOG_SEPARATOR)
    
    # Summary message
    action_word = "processed" if dry_run else "deleted"
    if stats['successful'] > 0:
        logger.info(f"✅ Successfully {action_word} {stats['successful']} {collection_name}s!")
    if stats['failed'] > 0:
        logger.warning(f"⚠️ {stats['failed']} {collection_name}s failed to delete")
        
    logger.info(f"🚀 All done with {collection_name}s")


def main() -> None:
    """Main function to orchestrate the Bluesky cleanup process.
    
    Validates environment, sets up logging, authenticates with Bluesky,
    and processes posts, reposts, and likes for deletion based on age.
    """
    try:
        # Environment validation and setup
        validate_environment()
        logger = setup_logging()
        
        # Log startup configuration
        dry_run = os.getenv("DRY_RUN", DEFAULT_DRY_RUN).lower() == "true"
        days_ago = os.getenv("DAYS_AGO", str(DEFAULT_DAYS_AGO))
        mode = "DRY RUN" if dry_run else "LIVE DELETION"
        
        logger.info("🚀 Starting Bluesky Content Cleanup Tool")
        logger.info(f"⚙️ Configuration: {mode} mode, processing items older than {days_ago} days")
        logger.info(LOG_SEPARATOR)
        
        # Authentication
        client, repo = authenticate_client(logger)
        logger.info(f"👤 Processing content for user: {repo}")
        logger.info(LOG_SEPARATOR)
        
        # Process each collection type
        collections = ["post", "repost", "like"]
        overall_start_time = datetime.now()
        
        for collection in collections:
            try:
                collection_start_time = datetime.now()
                logger.info(f"📂 Processing {collection}s...")
                
                fetch_and_process(collection, client, repo, logger)
                
                collection_duration = datetime.now() - collection_start_time
                logger.info(f"⏱️ {collection.title()} processing completed in {collection_duration.total_seconds():.1f} seconds")
                logger.info(LOG_SEPARATOR)
                
            except Exception as e:
                logger.error(f"💥 Critical error processing {collection}s: {e}")
                logger.error(f"🔄 Continuing with next collection type...")
                continue
        
        # Final summary
        total_duration = datetime.now() - overall_start_time
        logger.info("🎉 Bluesky Content Cleanup completed successfully!")
        logger.info(f"⏱️ Total execution time: {total_duration.total_seconds():.1f} seconds")
        
        if dry_run:
            logger.warning("🔄 This was a DRY RUN - no actual deletions were performed")
            logger.info("💡 Set DRY_RUN=false to perform actual deletions")
        else:
            logger.info("✅ All deletion operations completed")
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Process interrupted by user (Ctrl+C)")
        logger.info("🛑 Cleanup stopped gracefully")
    except SystemExit:
        # Re-raise SystemExit to preserve exit codes
        raise
    except Exception as e:
        logger.error(f"💀 Critical error in main process: {e}")
        logger.error("🚨 Bluesky Content Cleanup failed")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
