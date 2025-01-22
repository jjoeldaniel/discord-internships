from job import JobPosting
import base64
import requests
import shutil
from loguru import logger
import os
import json
from dotenv import load_dotenv

# Load environment variables
_ = load_dotenv()

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_ROUTE = "SimplifyJobs/Summer2025-Internships"
LISTING_URL = f"https://api.github.com/repos/{REPO_ROUTE}/contents/.github/scripts/listings.json"
LISTING_PATH = "listings.json"
PREVIOUS_LISTING_PATH = "previous_listings.json"

# By default, we ignore existing job posts that
# are made active after a period of inactivity
#
# Only fresh posts are included
INCLUDE_REPOSTS = False


def parse_file(path: str) -> list[JobPosting]:
    """
    Parse JSON file to `list[JobPosting]`
    """

    with open(path, "r") as f:
        data = list([JobPosting(**x) for x in json.load(f)])

    return data


def pull_data() -> list[JobPosting]:
    """
    Retrieve updated `JobPosting` list from GitHub,
    fully authenticated and without using raw.githubusercontent.com,
    so we get the higher API rate limits.
    """
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or "YOUR_PERSONAL_ACCESS_TOKEN"
    if not GITHUB_TOKEN:
        raise RuntimeError("No GitHub token found in environment or code.")

    # 1) GET file metadata via the 'contents' endpoint
    #    This remains on api.github.com, so we see X-RateLimit-* headers and stay authenticated.
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Optional: If we want to handle ETags (conditional requests),
    # we could add:
    #   headers["If-None-Match"] = 'W/"some-previous-etag"'
    # or handle them after this request.

    resp = requests.get(LISTING_URL, headers=headers)
    resp.raise_for_status()

    info = resp.json()
    file_sha = info["sha"]

    blob_url = f"https://api.github.com/repos/{REPO_ROUTE}/git/blobs/{file_sha}"
    blob_resp = requests.get(blob_url, headers=headers)
    blob_resp.raise_for_status()
    blob_info = blob_resp.json()

    decoded_bytes = base64.b64decode(blob_info["content"])

    # Write the JSON to a local file
    with open(LISTING_PATH, "wb") as f:
        _ = f.write(decoded_bytes)

    # Now parse the local JSON
    return parse_file(LISTING_PATH)


def get_new_roles() -> list[JobPosting]:
    """
    Retrieve new or newly active roles
    """

    # Pull new data
    new_data: list[JobPosting] = pull_data()

    new_roles: list[JobPosting] = []

    # Check if PREVIOUS_LISTING_PATH exists
    # If not, initialize and return empty
    if not os.path.exists(PREVIOUS_LISTING_PATH):
        logger.info(f"File {PREVIOUS_LISTING_PATH} not found. Initializing file..")
        shutil.copy(LISTING_PATH, PREVIOUS_LISTING_PATH)
        return new_roles

    # Build a dictionary of old roles keyed by their ID
    old_dict = {job.id: job for job in parse_file(PREVIOUS_LISTING_PATH)}

    # Iterate over new postings
    for new_post in new_data:
        old_post = old_dict.get(new_post.id)

        # If job didn't exist before, it's new
        if not old_post:
            new_roles.append(new_post)
        # Otherwise, check if it just became active
        else:
            # If old was inactive, but new is active, it's newly active
            if INCLUDE_REPOSTS and (not old_post.active and new_post.active):
                new_roles.append(new_post)

    # Update previous roles file
    shutil.copy(LISTING_PATH, PREVIOUS_LISTING_PATH)

    return new_roles
