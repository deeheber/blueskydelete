import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from atproto import Client

load_dotenv()

# Login
print("Logging in...⏳")
client = Client()

try:
  client.login(os.getenv("USERNAME"), os.getenv("PASSWORD"))
  print("Login successful! 😎\n")
except Exception as e:
  print(f"Failed to login: {e}")
  exit()

# Get posts up until three months ago
today = datetime.now()
# TODO edit this to change the time frame if desired
three_months_ago = today - timedelta(days=90)

try:
  result = client.app.bsky.feed.search_posts(params={"q": "*", "author": os.getenv("USERNAME"), "until": three_months_ago.strftime("%Y-%m-%dT%H:%M:%SZ")})
  
  print(f"Fetched {len(result.posts)} posts ⭐️\n")
except Exception as e:
  print(f"Failed to fetch posts: {e}")
  exit()

# Delete posts returned from the previous query
delete_flag = os.getenv("DELETE_POSTS")
for post in result.posts:
  if delete_flag == "true":
    try:
      print(f"Deleting post {post.record.text}...")
      client.delete_post(post.uri)
      print("Post deleted successfully! 🎉")
    except Exception as e:
      print(f"Failed to delete post: {e}")
  else:
    print(f"Dry run...this would delete post {post.record.text}")
    # print(post.model_dump_json())

  print("#################")

print("All done! 🚀")

