import os
from datetime import datetime, timedelta
from atproto import Client, exceptions

if not os.getenv("CI"):
  from dotenv import load_dotenv
  load_dotenv()

# Set Variables
client = Client()
repo = os.getenv("USERNAME")
collection = "app.bsky.feed.repost"

# Login
print("Logging in...⏳")

try:
  client.login(repo, os.getenv("PASSWORD"))
  print("Login successful! 😎\n")
except exceptions.AtProtocolError as e:
  print(f"Failed to login: {e}")
  exit()

# Fetch all reposts (the API doesn't have a way to filter currently 👎🏻)
try:
  reposts = []
  cursor = None

  while True:
    result = client.com.atproto.repo.list_records(
      params={
        "repo": repo,
        "collection": collection,
        "limit": 100,
        "cursor": cursor,
        "reverse": True,
      }
    )

    reposts.extend(result.records)

    if not result.cursor:
      break
    cursor = result.cursor

  print(f"Fetched {len(reposts)} reposts total ⭐️\n")
except exceptions.AtProtocolError as e:
  print(f"Failed to get posts: {e}")
  exit()

# Get reposts up until x days ago and delete if not a dry run
# Default is 90 days
today = datetime.now()
num_days = int(os.getenv("DAYS_AGO", 90))
days_ago = today - timedelta(days=num_days)
time_format  = "%Y-%m-%dT%H:%M:%S.%fZ"
target_date_str = days_ago.strftime(time_format)
print(f"Target date: {target_date_str}...🗓️\n")
target_date = datetime.strptime(target_date_str, time_format)

num_reposts_deleted = 0
dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

for repost in reposts:
  # Break early to save some cycles if current post is after target date
  if (datetime.strptime(repost.value.created_at, time_format) > target_date):
    break

  if dry_run == False:
    try:
      print(f"Deleting repost...⏳\n\nuri: {repost.uri}\ncreated_at: {repost.value.created_at}")
      client.delete_repost(repost.uri)
      print("Repost deleted successfully! 🎉")
    except exceptions.AtProtocolError as e:
      print(f"Failed to delete repost: {e}")
  else:
    # Print full repost commented out but keeping for debugging
    # print(repost.model_dump_json(indent=2))
    print(f"Dry run, if run for real this would delete repost...⏳\n\nuri: {repost.uri}\ncreated_at: {repost.value.created_at}")

  print("########################################")
  num_reposts_deleted += 1

print(f"{num_reposts_deleted} posts {'deleted' if dry_run == False else 'processed'}!")
print("All done! 🚀")
