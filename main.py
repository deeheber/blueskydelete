import os
from datetime import datetime, timedelta
from atproto import Client, exceptions

if os.getenv("CI"):
  print("Running in CI...skipping dotenv import.")
else:
  from dotenv import load_dotenv
  load_dotenv()

# Set Variables
client = Client()
repo = os.getenv("USERNAME")

# Login
print("Logging in...⏳")

try:
  client.login(repo, os.getenv("PASSWORD"))
  print("Login successful! 😎\n")
except exceptions.AtProtocolError as e:
  print(f"Failed to login: {e}")
  exit()

def fetch_and_process(collection_name):
  # Fetch items
  collection_url = "app.bsky.feed." + collection_name

  print(f"Starting to process {collection_name}s 🏁\n")
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

    print(f"Fetched {len(items)} {collection_name}s total ⭐️\n")
  except exceptions.AtProtocolError as e:
    print(f"Failed to get {collection_name}s: {e}")
    exit()

  num_days = int(os.getenv("DAYS_AGO", 90))
  target_date = datetime.now() - timedelta(days=num_days)
  print(f"Target date: {target_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}...🗓️\n")

  client_method="delete_" + collection_name
  num_deleted = 0
  dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

  for item in items:
    # Break early to save some cycles if current post is after target date
    if (datetime.strptime(item.value.created_at, "%Y-%m-%dT%H:%M:%S.%fZ") > target_date):
      break

    if dry_run == False:
      try:
        print(f"Deleting {collection_name}s...⏳")
        print(item.model_dump_json(indent=2))
        getattr(client, client_method)(item.uri)
        print(f"{collection_name.title()} deleted successfully! 🎉")
      except exceptions.AtProtocolError as e:
        print(f"Failed to delete {collection_name}s: {e}")
    else:
      print(f"Dry run, if run for real this would delete {collection_name}...⏳")
      print(item.model_dump_json(indent=2))

    print("=" * 75)
    num_deleted += 1

  print(f"{num_deleted} {collection_name}s {'deleted' if dry_run == False else 'processed'}!")
  print(f"All done with {collection_name}s ✅🚀\n")

fetch_and_process("post")
fetch_and_process("repost")
fetch_and_process("like")
