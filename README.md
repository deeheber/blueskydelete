# blueskydelete

Recreating some of the functionality of https://tweetdelete.net/, but for bluesky.

Currently the script searches for posts (including replies) of the currently logged in user from the beginning up until three months ago and deletes them.

The goal is to only have posts that are at most three months old (but the three months is configurable via env vars).

## Quick Start (instructions are for on a Mac)

1. Clone this repo
2. Check the `.python-version` file for the version of python to use. Other versions might work, but this is the verison used during creation.
3. Create a virtual environment: `python3 -m venv .venv`
4. Activate the virtual environment: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Get env vars set up: `touch .env & cp .env.sample .env` and change the values in the created `.env`. Note that setting the `DELETE_POSTS` to true will actually delete the posts (be careful). Omitting or setting to false will print what will be deleted as a dry run.
7. Run script: `python main.py`

## Future Improvement/Feature Ideas

This is admittedly pretty simple and bare bones.

1. Explore using the `requests` library directly to make http calls instead of the `atproto` wrapper
2. Add in the ability to delete likes and reposts
