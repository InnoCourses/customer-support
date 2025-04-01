import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

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
ADMIN_BOT_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN")

# Initialize bot and dispatcher with FSM storage
storage = MemoryStorage()
bot = Bot(token=ADMIN_BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Initialize API client
api_client = ApiClient(API_BASE_URL)

# Define states for conversation handling


class AdminStates(StatesGroup):
    in_issue = State()  # Admin is currently working on an issue


class CustomerSupportAdminBot:
    def __init__(self):
        # Register handlers
        self.register_handlers()

    def register_handlers(self):
        dp.register_message_handler(self.start_command, Command("start"))
        dp.register_message_handler(self.help_command, Command("help"))
        dp.register_message_handler(self.register_command, Command("register"))
        dp.register_message_handler(self.list_issues_command, Command("issues"))
        dp.register_message_handler(
            self.exit_issue_command, Command("exit"), state=AdminStates.in_issue
        )

        # Register callback query handler for inline buttons
        dp.register_callback_query_handler(
            self.button_callback, lambda c: c.data.startswith("issue:")
        )

        # Register message handler for issue conversation
        dp.register_message_handler(
            self.handle_message,
            state=AdminStates.in_issue,
            content_types=types.ContentTypes.TEXT,
        )

    async def start_command(self, message: types.Message):
        """Send a message when the command /start is issued."""
        await message.reply(
            "Welcome to the Customer Support Admin Bot! 🛡️\n\n"
            "Use /register to register yourself as an admin.\n"
            "Use /issues to list all open issues.\n"
            "Use /exit to exit the current issue conversation.\n"
            "Use /help to see all available commands."
        )

    async def help_command(self, message: types.Message):
        """Send a message when the command /help is issued."""
        await message.reply(
            "Here are the available commands:\n\n"
            "/start - Start the bot\n"
            "/register - Register yourself as an admin\n"
            "/issues - List all open issues\n"
            "/exit - Exit the current issue conversation\n"
            "/help - Show this help message"
        )

    async def register_command(self, message: types.Message):
        """Register the user as an admin."""
        chat_id = str(message.chat.id)
        username = message.from_user.username or f"admin_{chat_id}"

        try:
            # Register admin
            admin_response = await api_client.register_admin(chat_id, f"@{username}")
            await message.reply(
                f"You have been registered as an admin! (ID: {admin_response.admin_id})\n\n"
                f"You will now receive notifications for issues requiring manual attention."
            )
        except ApiClientError as e:
            if e.status_code == 400:
                # Already registered
                await message.reply(
                    "You are already registered as an admin.\n"
                    "Use /issues to list all open issues."
                )
            else:
                logger.error(f"Error in register_command: {e}")
                await message.reply(
                    "Sorry, I couldn't register you as an admin due to a technical issue. Please try again later."
                )

    async def list_issues_command(self, message: types.Message):
        """List all open issues."""
        try:
            # Get only manual issues
            issues = await api_client.get_manual_issues()

            if not issues:
                await message.reply(
                    "There are no issues requiring manual assistance at the moment."
                )
                return

            # Create inline keyboard with issues
            keyboard = []
            for issue in issues:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"Issue #{issue.issue_id} (manual)",
                            callback_data=f"issue:{issue.issue_id}",
                        )
                    ]
                )

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await message.reply(
                f"Found {len(issues)} issues requiring manual assistance\n\nSelect an issue to view and respond:",
                reply_markup=reply_markup,
            )
        except ApiClientError as e:
            logger.error(f"Error in list_issues_command: {e}")
            await message.reply(
                "Sorry, I couldn't fetch the issues due to a technical issue. Please try again later."
            )

    async def exit_issue_command(self, message: types.Message, state: FSMContext):
        """Exit the current issue conversation."""
        # Get current state data
        data = await state.get_data()
        issue_id = data.get("active_issue_id")

        # Reset state
        await state.finish()

        if issue_id:
            await message.reply(
                f"You have exited the conversation for Issue #{issue_id}.\n"
                f"Use /issues to list all open issues."
            )
        else:
            await message.reply(
                "You are not currently in any issue conversation.\n"
                "Use /issues to list all open issues."
            )

    async def button_callback(
        self, callback_query: types.CallbackQuery, state: FSMContext
    ):
        """Handle button callbacks."""
        await callback_query.answer()

        # Extract issue ID from callback data
        issue_id = callback_query.data.split(":")[1]

        # Set state to indicate admin is in an issue conversation
        await AdminStates.in_issue.set()

        # Store issue ID in state
        await state.update_data(active_issue_id=issue_id)

        # Fetch and display issue details
        await self.fetch_and_display_issue(callback_query.message, issue_id)

    async def fetch_and_display_issue(self, message: types.Message, issue_id: str):
        """Fetch and display issue details."""
        try:
            # Get issue messages
            issue_with_messages = await api_client.get_issue_messages(issue_id)

            # Format messages
            messages_text = "\n\n".join(
                f"[{msg.from_user}]\n{msg.text}" for msg in issue_with_messages.messages
            )

            response_text = (
                f"Issue #{issue_id}\n\n"
                f"Messages:\n{messages_text}\n\n"
                f"Reply to this message to respond to the user.\n"
                f"Use /exit to exit this conversation."
            )

            # If message is a callback result, edit it, otherwise send new message
            if hasattr(message, "edit_text"):
                await message.edit_text(response_text)
            else:
                await message.reply(response_text)
        except ApiClientError as e:
            logger.error(f"Error in fetch_and_display_issue: {e}")
            error_message = "Sorry, I couldn't fetch the issue due to a technical issue. Please try again later."

            if hasattr(message, "edit_text"):
                await message.edit_text(error_message)
            else:
                await message.reply(error_message)

    async def handle_message(self, message: types.Message, state: FSMContext):
        """Handle admin messages and forward them to the issue."""
        # Get current state data
        data = await state.get_data()
        issue_id = data.get("active_issue_id")

        if not issue_id:
            await message.reply(
                "You are not currently in any issue conversation.\n"
                "Use /issues to list all open issues."
            )
            await state.finish()
            return

        message_text = message.text

        # Ignore commands
        if message_text.startswith("/"):
            return

        # Send message to the issue
        try:
            await api_client.add_admin_message(issue_id, message_text)
        except ApiClientError as e:
            logger.error(f"Error in handle_message: {e}")
            await message.reply(
                "Sorry, I couldn't send your message due to a technical issue. Please try again later."
            )


async def handle_manual_mode(data):
    """Handle issue switched to manual mode from realtime events"""
    try:
        issue_id = data.get("id")
        username = data.get("username", "Unknown user")

        if not issue_id:
            logger.error(f"Invalid manual mode data: {data}")
            return

        # Create inline keyboard for quick action
        keyboard = [
            [InlineKeyboardButton("View Issue", callback_data=f"issue:{issue_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Get all registered admins
        admins = await api_client.get_all_admins()

        # Send notification to all admins
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_chat_id,
                    text=f"Manual assistance requested!\n\n"
                    f"Issue ID: {issue_id}\n"
                    f"User: {username}\n\n"
                    f"Click below to view and respond:",
                    reply_markup=reply_markup,
                )
                logger.info(f"Sent manual mode notification to admin {admin_chat_id}")
            except Exception as e:
                logger.error(
                    f"Error sending notification to admin {admin_chat_id}: {e}"
                )
    except Exception as e:
        logger.error(f"Error handling manual mode: {e}")


async def handle_new_message(data):
    """Handle new user message from realtime events"""
    try:
        issue_id = data.get("issue_id")
        message_data = data.get("message", {})

        if not issue_id or not message_data:
            logger.error(f"Invalid new message data: {data}")
            return

        # Get message details
        from_user = message_data.get("from_user", "Unknown")
        text = message_data.get("text", "")

        # Create inline keyboard for quick action
        keyboard = [
            [InlineKeyboardButton("View Issue", callback_data=f"issue:{issue_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        try:
            # Get issue to verify it's in manual mode
            issue = await api_client.get_issue(issue_id)

            # Only send notifications for manual issues
            if issue.status != "manual":
                logger.info(f"Skipping notification for non-manual issue {issue_id}")
                return

            # Get all admins
            admins = await api_client.get_all_admins()

            # Send notifications to all admins
            for admin in admins:
                state = await dp.current_state(chat=admin.telegram_chat_id).get_data()

                print(state)
                admin_chat_id = admin.telegram_chat_id
                try:
                    # Check if this admin is already working on this issue
                    if state.get("active_issue_id") == issue_id:
                        # Send simple message without buttons for admins already working on this issue
                        await bot.send_message(chat_id=admin_chat_id, text=text)
                        logger.info(
                            f"Sent simple update to admin {admin_chat_id} already working on issue {issue_id}"
                        )
                    else:
                        # Send full notification with buttons for other admins
                        await bot.send_message(
                            chat_id=admin_chat_id,
                            text=f"New message in Manual Issue #{issue_id}\n\n"
                            f"From: {from_user}\n"
                            f"Message: {text}\n\n"
                            f"Click below to view and respond:",
                            reply_markup=reply_markup,
                        )
                        logger.info(
                            f"Sent notification with button to admin {admin_chat_id}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error sending notification to admin {admin_chat_id}: {e}"
                    )
        except ApiClientError as e:
            logger.error(f"Error getting issue in handle_new_message: {e}")
    except Exception as e:
        logger.error(f"Error handling new message: {e}")


def main():
    """Start the bot."""
    from database.realtime_handler import realtime_handler

    # Create bot instance
    admin_bot = CustomerSupportAdminBot()

    # Register callbacks for realtime events
    realtime_handler.register_manual_mode_callback(handle_manual_mode)
    realtime_handler.register_new_message_callback(handle_new_message)

    # Start realtime handler
    loop = asyncio.get_event_loop()
    loop.create_task(realtime_handler.start())

    # Start bot
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
