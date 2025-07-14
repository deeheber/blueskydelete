import os
import logging
from datetime import datetime, timedelta
from atproto import Client, exceptions

if os.getenv("CI"):
  print("Running in CI...skipping dotenv import.")
else:
  from dotenv import load_dotenv
  load_dotenv()

# Configure logging after dotenv is loaded
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"ℹ️ Log level set to {log_level}")

# Set Variables
client = Client()
repo = os.getenv("USERNAME")

# Login
logger.info("⏳ Logging in...")

try:
  client.login(repo, os.getenv("PASSWORD"))
  logger.info("😎 Login successful!")
except exceptions.AtProtocolError as e:
  logger.error(f"Failed to login: {e}")
  exit()

def fetch_and_process(collection_name):
  # Fetch items
  collection_url = "app.bsky.feed." + collection_name

  logger.info(f"🏁 Starting to process {collection_name}s")
  try:
    items = []
    cursor = None

    while True:
      result = client.com.atproto.repo.list_records(
        params={
          "repo": repo,
          "collection": collection_url,
          "limit": 100,
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
    exit()

  num_days = int(os.getenv("DAYS_AGO", 90))
  target_date = datetime.now() - timedelta(days=num_days)
  logger.info(f"🗓️ Target date: {target_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}")

  client_method="delete_" + collection_name
  num_deleted = 0
  dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

  for item in items:
    # Break early to save some cycles if current post is after target date
    if (datetime.strptime(item.value.created_at, "%Y-%m-%dT%H:%M:%S.%fZ") > target_date):
      break

    if dry_run == False:
      try:
        logger.info(f"⏳ Deleting {collection_name}:{item.uri}...")
        logger.debug(item.model_dump_json(indent=2))
        getattr(client, client_method)(item.uri)
        logger.info(f"🎉 {collection_name.title()} deleted successfully!")
      except exceptions.AtProtocolError as e:
        logger.error(f"Failed to delete {collection_name}s: {e}")
    else:
      logger.warning(f"⏳ Dry run, if run for real this would delete {collection_name} with uri {item.uri}...")
      logger.warning(item.model_dump_json(indent=2))

    logger.info("=" * 75)
    num_deleted += 1

  logger.info(f"✅ {num_deleted} {collection_name}s {'deleted' if dry_run == False else 'processed'}!")
  logger.info(f"🚀 All done with {collection_name}s")

fetch_and_process("post")
fetch_and_process("repost")
fetch_and_process("like")
