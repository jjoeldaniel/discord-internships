from time import sleep
from dotenv import load_dotenv
import os
from loguru import logger
from discord_webhook import DiscordWebhook, DiscordEmbed
from job import JobPosting
from roles import get_new_roles

# Load environment variables
_ = load_dotenv()

# Constants
WEBHOOK_URLS: list[str] = str(os.getenv("WEBHOOK_URLS")).split(",")


def main():
    if not WEBHOOK_URLS:
        logger.error("No WEBHOOK_URLS given. Please add at least one before running..")
        os._exit(1)

    while True:
        logger.info("Checking for new roles")

        # Wait some time before checking again
        new_roles: list[JobPosting] = get_new_roles()

        if new_roles:
            logger.success(f"{len(new_roles)} new role(s) found")

        while new_roles:
            webhooks = DiscordWebhook.create_batch(urls=WEBHOOK_URLS)

            for _ in range(0, 9):
                if not new_roles:
                    break

                role = new_roles.pop()

                embed = DiscordEmbed(
                    description=f"## [{role.title} @ {role.company_name}]({role.url})",
                    color="03b2f8",
                )

                embed.add_embed_field(
                    name="**Location(s)**",
                    value=", ".join(role.locations) if role.locations else "N/A",
                    inline=False,
                )
                embed.add_embed_field(
                    name="**Sponsorship**",
                    value=role.sponsorship or "N/A",
                    inline=False,
                )

                [webhook.add_embed(embed) for webhook in webhooks]

            for webhook in webhooks:
                try:
                    _ = webhook.execute()
                except Exception as e:
                    print(e)

        sleep(300)


if __name__ == "__main__":
    main()
