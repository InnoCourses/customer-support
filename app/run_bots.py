import os
import logging
import multiprocessing
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
USER_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN")


def run_user_bot():
    """Run the user bot in a separate process"""
    logger.info("Starting User Bot...")
    from telegram.aiogram_bot import main

    main()


def run_admin_bot():
    """Run the admin bot in a separate process"""
    logger.info("Starting Admin Bot...")
    from telegram.aiogram_admin_bot import main

    main()


def main():
    """Run both bots in separate processes"""
    print("\n=== Starting Customer Support Bots ===\n")
    print(f"User Bot Token: {USER_BOT_TOKEN[:5]}...")
    print(f"Admin Bot Token: {ADMIN_BOT_TOKEN[:5]}...\n")
    print("Both bots are now running!")
    print("Press Ctrl+C to stop the bots\n")

    # Start bots in separate processes
    user_process = multiprocessing.Process(target=run_user_bot)
    admin_process = multiprocessing.Process(target=run_admin_bot)

    user_process.start()
    admin_process.start()

    try:
        # Wait for both processes to finish
        user_process.join()
        admin_process.join()
    except KeyboardInterrupt:
        print("\nExiting...")
        user_process.terminate()
        admin_process.terminate()
        user_process.join()
        admin_process.join()


if __name__ == "__main__":
    main()
