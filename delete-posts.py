import os
from datetime import datetime, timedelta
from atproto import Client, exceptions

if not os.getenv("CI"):
  from dotenv import load_dotenv
  load_dotenv()

# Login
print("Logging in...⏳")
client = Client()

try:
  client.login(os.getenv("USERNAME"), os.getenv("PASSWORD"))
  print("Login successful! 😎\n")
except exceptions.AtProtocolError as e:
  print(f"Failed to login: {e}")
  exit()

# Get posts up until x days ago
# Default is 90 days
today = datetime.now()
num_days = int(os.getenv("DAYS_AGO", 90))
days_ago = today - timedelta(days=num_days)

try:
  posts = []
  cursor = None

  while True:
    result = client.app.bsky.feed.search_posts(params={"q": "*", "author": os.getenv("USERNAME"), "until": days_ago.strftime("%Y-%m-%dT%H:%M:%SZ"), "cursor": cursor})

    posts.extend(result.posts)

    if not result.cursor:
      break
    cursor = result.cursor

  print(f"Fetched {len(posts)} posts ⭐️\n")
except exceptions.AtProtocolError as e:
  print(f"Failed to fetch posts: {e}")
  exit()

# Delete posts returned from the previous query
dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
for post in posts:
  if dry_run == False:
    try:
      print(f"Deleting post \n\n{post.record.text}...⏳")
      client.delete_post(post.uri)
      print("Post deleted successfully! 🎉")
    except exceptions.AtProtocolError as e:
      print(f"Failed to delete post: {e}")
  else:
    print(f"Dry run...this would delete post \n\n{post.record.text}")

  print("########################################")
print(f"{len(posts)} posts {'deleted' if dry_run == False else 'processed'}!")
print("All done! 🚀")

