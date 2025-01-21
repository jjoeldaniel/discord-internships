from job import JobPosting
import requests
import shutil
from loguru import logger
import os
import json

REPO_ROUTE = "SimplifyJobs/Summer2025-Internships"
LISTING_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
LISTING_PATH = "listings.json"
PREVIOUS_LISTING_PATH = "previous_listings.json"

# NEW: Local file to store the last known ETag for conditional requests
LISTING_ETAG_PATH = "listings.etag"

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
    Retrieve updated `JobPosting` list using a conditional request.
    If no changes, returns existing local copy (if present) or an empty list.
    """

    # Read the last known ETag if it exists
    old_etag = None
    if os.path.exists(LISTING_ETAG_PATH):
        with open(LISTING_ETAG_PATH, "r") as f:
            old_etag = f.read().strip()

    # Include the ETag in the If-None-Match header
    headers = {}
    if old_etag:
        headers["If-None-Match"] = old_etag

    # Fetch file info from GitHub (raw URL still works with ETag)
    r = requests.get(LISTING_URL, headers=headers)

    if r.status_code == 304:
        logger.info("No changes in listings file (304 Not Modified).")
        return []

    elif r.status_code == 200:
        # The file was updated or no ETag was sent; we have new content
        new_etag = r.headers.get("ETag")
        if new_etag:
            with open(LISTING_ETAG_PATH, "w") as f:
                _ = f.write(new_etag)

        # Overwrite the local file
        try:
            os.remove(LISTING_PATH)
        except OSError:
            pass

        with open(LISTING_PATH, "w") as f:
            json.dump(r.json(), f)

        return parse_file(LISTING_PATH)
    else:
        r.raise_for_status()
        return []


def get_new_roles() -> list[JobPosting]:
    """
    Retrieve new or newly active roles
    """

    # Pull new data
    new_data: list[JobPosting] = pull_data()
    new_roles: list[JobPosting] = []

    if not new_data:
        return []

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
