import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command

from telegram.client.api_client import ApiClient, ApiClientError

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Initialize API client
api_client = ApiClient(API_BASE_URL)


class CustomerSupportBot:
    def __init__(self):
        # Register handlers
        self.register_handlers()

    def register_handlers(self):
        dp.register_message_handler(self.start_command, Command("start"))
        dp.register_message_handler(self.help_command, Command("help"))
        dp.register_message_handler(self.new_issue_command, Command("new"))
        dp.register_message_handler(self.status_command, Command("status"))
        dp.register_message_handler(self.manual_command, Command("manual"))
        dp.register_message_handler(self.close_command, Command("close"))
        dp.register_message_handler(
            self.handle_message, content_types=types.ContentTypes.TEXT
        )

    async def start_command(self, message: types.Message):
        """Send a message when the command /start is issued."""
        await message.reply(
            "Welcome to the Customer Support Bot! 👋\n\n"
            "Use /new to create a new support request.\n"
            "Use /status to check your current request status.\n"
            "Use /manual to request human assistance.\n"
            "Use /close to close your current issue.\n"
            "Use /help to see all available commands."
        )

    async def help_command(self, message: types.Message):
        """Send a message when the command /help is issued."""
        await message.reply(
            "Here are the available commands:\n\n"
            "/start - Start the bot\n"
            "/new - Create a new support request\n"
            "/status - Check your current request status\n"
            "/manual - Request human assistance\n"
            "/help - Show this help message"
        )

    async def new_issue_command(self, message: types.Message):
        """Create a new support issue."""
        chat_id = str(message.chat.id)
        username = message.from_user.username or f"user_{chat_id}"

        try:
            # Check if user already has an open issue
            existing_issue = await api_client.get_user_issue(chat_id)
            if existing_issue:
                await message.reply(
                    f"You already have an active support request (ID: {existing_issue.issue_id}).\n"
                    f"Current status: {existing_issue.status}\n\n"
                    f"Just send your messages and I'll help you!"
                )
                return

            # Create new issue
            new_issue = await api_client.create_issue(chat_id, f"@{username}")
            await message.reply(
                f"Support request created successfully! (ID: {new_issue.issue_id})\n\n"
                f"Please describe your issue, and I'll do my best to help you."
            )

        except ApiClientError as e:
            logger.error(f"Error in new_issue_command: {e}")
            await message.reply(
                "Sorry, I couldn't create a support request due to a technical issue. Please try again later."
            )

    async def status_command(self, message: types.Message):
        """Check the status of the user's current issue."""
        chat_id = str(message.chat.id)

        try:
            issue = await api_client.get_user_issue(chat_id)
            if issue:
                status_text = {
                    "open": "Active (AI assistance)",
                    "manual": "Active (Human assistance)",
                    "closed": "Closed",
                }.get(issue.status, issue.status)

                await message.reply(
                    f"Your support request (ID: {issue.issue_id})\n"
                    f"Status: {status_text}"
                )
            else:
                await message.reply(
                    "You don't have any active support requests.\n"
                    "Use /new to create one."
                )
        except ApiClientError as e:
            logger.error(f"Error in status_command: {e}")
            await message.reply(
                "Sorry, I couldn't check your support request status due to a technical issue. Please try again later."
            )

    async def manual_command(self, message: types.Message):
        """Switch to manual support mode."""
        chat_id = str(message.chat.id)

        try:
            # Check if user has an open issue
            issue = await api_client.get_user_issue(chat_id)
            if issue:
                # Switch to manual mode
                await api_client.switch_to_manual(issue.issue_id)
                await message.reply(
                    "Your request has been escalated to our support team.\n"
                    "A human agent will assist you shortly."
                )
            else:
                await message.reply(
                    "You don't have any active support requests.\n"
                    "Use /new to create one."
                )
        except ApiClientError as e:
            logger.error(f"Error in manual_command: {e}")
            await message.reply(
                "Sorry, I couldn't process your request due to a technical issue. Please try again later."
            )
            
    async def close_command(self, message: types.Message):
        """Close the current support issue."""
        chat_id = str(message.chat.id)
        
        try:
            # Check if user has an open issue
            issue = await api_client.get_user_issue(chat_id)
            if issue:
                # Close the issue
                closed_issue = await api_client.close_user_issue(issue.issue_id)
                await message.reply(
                    f"Your support request (ID: {closed_issue.issue_id}) has been closed.\n"
                    f"Thank you for using our support service!"
                )
            else:
                await message.reply(
                    "You don't have any active support requests to close.\n"
                    "Use /new to create one."
                )
        except ApiClientError as e:
            logger.error(f"Error in close_command: {e}")
            await message.reply(
                "Sorry, I couldn't close your support request due to a technical issue. Please try again later."
            )

    async def handle_message(self, message: types.Message):
        """Handle user messages and forward them to the API."""
        chat_id = str(message.chat.id)
        message_text = message.text

        # Ignore commands
        if message_text.startswith("/"):
            return

        try:
            # Check if user has an active issue
            issue = await api_client.get_user_issue(chat_id)
            if issue:
                # Send message to API
                response = await api_client.add_user_message(
                    issue.issue_id, message_text
                )
                if response:
                    await message.reply(response.text)
            else:
                # No active issue
                await message.reply(
                    "You don't have an active support request.\n"
                    "Use /new to create one."
                )
        except ApiClientError as e:
            logger.error(f"Error in handle_message: {e}")
            await message.reply(
                "Sorry, I couldn't process your message due to a technical issue. Please try again later."
            )


async def handle_admin_message(data):
    """Handle admin message from realtime events"""
    try:
        telegram_chat_id = data.get("telegram_chat_id")
        message_data = data.get("message", {})

        if not telegram_chat_id or not message_data:
            logger.error(f"Invalid admin message data: {data}")
            return

        # Send message to user
        text = message_data.get("text", "")
        await bot.send_message(chat_id=telegram_chat_id, text=text)
        logger.info(f"Sent admin message to user {telegram_chat_id}")
    except Exception as e:
        logger.error(f"Error handling admin message: {e}")


def main():
    """Start the bot."""
    from database.realtime_handler import realtime_handler

    # Create bot instance
    customer_bot = CustomerSupportBot()

    # Register callback for admin messages
    realtime_handler.register_admin_message_callback(handle_admin_message)

    # Start realtime handler
    loop = asyncio.get_event_loop()
    loop.create_task(realtime_handler.start())

    # Start bot
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
