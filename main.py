from time import sleep
from dotenv import load_dotenv
import os
import shutil
from loguru import logger
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
import json
from job import JobPosting

# Load environment variables
_ = load_dotenv()

# Constants
WEBHOOK_URLS: list[str] = str(os.getenv("WEBHOOK_URLS")).split(",")
REPO_ROUTE = "SimplifyJobs/Summer2025-Internships"
LISTING_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
LISTING_PATH = "listings.json"
PREVIOUS_LISTING_PATH = "previous_listings.json"

# By default, we ignore existing job posts that
# are made active after a period of inactivity
#
# Only fresh posts are included
INCLUDE_REPOSTS = True


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


def main():
    if not WEBHOOK_URLS:
        logger.error("No WEBHOOK_URLS given. Please add at least one before running..")
        os._exit(1)

    while True:
        logger.info("Checking for new roles")

        # Wait some time before checking again
        new_roles: list[JobPosting] = get_new_roles()

        if new_roles:
            logger.success("New roles found")

            webhooks = DiscordWebhook.create_batch(urls=WEBHOOK_URLS)

            for role in new_roles:
                embed = DiscordEmbed(
                    title=f"[{role.title} @ {role.company_name}]({role.url})",
                    color="03b2f8",
                )

                embed.add_embed_field(
                    name="Location(s)",
                    value=", ".join(role.locations) if role.locations else "N/A",
                    inline=False,
                )
                embed.add_embed_field(
                    name="Sponsorship", value=role.sponsorship or "N/A", inline=False
                )

                [webhook.add_embed(embed) for webhook in webhooks]

            _ = [webhook.execute() for webhook in webhooks]

        sleep(300)


if __name__ == "__main__":
    main()
