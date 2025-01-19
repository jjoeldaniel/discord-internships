import asyncio
from dotenv import load_dotenv
import os
from loguru import logger
import requests
import json
from job import JobPosting

# Load environment variables
_ = load_dotenv()

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_ROUTE = "SimplifyJobs/Summer2025-Internships"
LISTING_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
LISTING_PATH = "listings.json"
PREVIOUS_LISTING_PATH = "previous_listings.json"


def parse_file(path: str) -> list[JobPosting]:
    """
    Parse JSON file to `list[JobPosting]`
    """

    with open(path, "r") as f:
        data = list([JobPosting(**x) for x in json.load(f)])

    return data


def pull_data() -> list[JobPosting]:
    """
    Retrieve updated `JobPosting` list
    """

    try:
        os.remove(LISTING_PATH)
    except OSError:
        pass
    finally:
        data = requests.get(LISTING_URL)
        with open(LISTING_PATH, "w") as f:
            json.dump(data.json(), f)

        return parse_file(LISTING_PATH)


def get_new_roles() -> list[JobPosting]:
    """
    Retrieve new or newly active roles
    """

    # Pull new data
    new_data: list[JobPosting] = pull_data()

    new_roles: list[JobPosting] = []

    # Check if PREVIOUS_LISTING_PATH exists
    # If not, then return empty
    if not os.path.exists(PREVIOUS_LISTING_PATH):
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
            if not old_post.active and new_post.active:
                new_roles.append(new_post)

    return new_roles


async def main():
    while True:
        logger.info("Checking for new roles")

        # Wait some time before checking again
        new_roles: list[JobPosting] = get_new_roles()

        if new_roles:
            logger.success("New roles found")
            [print(role) for role in new_roles]

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
