import os
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Callable, List, Optional
from supabase.client import AsyncClient, create_async_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class RealtimeHandler:
    def __init__(self):
        # Event callbacks
        self.manual_mode_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.new_message_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.admin_message_callbacks: List[Callable[[Dict[str, Any]], None]] = []

        # Initialize async Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # Channels for realtime subscriptions
        self.client: AsyncClient = None
        self.issues_channel = None
        self.messages_channel = None

    async def start(self):
        """Start listening for realtime events"""
        logger.info("Starting realtime event handler...")

        # Create async Supabase client
        self.client = await create_async_client(self.supabase_url, self.supabase_key)

        # Subscribe to issues table for status changes
        self.issues_channel = self.client.channel("public:issues")
        await self.issues_channel.on_postgres_changes(
            event="UPDATE",
            schema="public",
            table="issues",
            callback=self._handle_issue_update_wrapper,
        ).subscribe()

        # Subscribe to messages table for new messages
        self.messages_channel = self.client.channel("public:messages")
        await self.messages_channel.on_postgres_changes(
            event="INSERT",
            schema="public",
            table="messages",
            callback=self._handle_message_update_wrapper,
        ).subscribe()

        logger.info("Realtime event handler started")

    def _handle_issue_update_wrapper(self, payload: Dict[str, Any]):
        """Wrapper for handling issue updates that creates a task"""
        asyncio.create_task(self._handle_issue_update(payload))

    async def _handle_issue_update(self, payload: Dict[str, Any]):
        """Handle issue updates"""
        logger.info(f"Received issue update: {payload}")

        # Check if status changed to manual
        new_record = payload.get("data", {}).get("record", {})
        old_record = payload.get("data", {}).get("old_record", {})

        if (
            new_record.get("status") == "manual"
            and old_record.get("status") != "manual"
        ):
            logger.info(f"Issue {new_record.get('id')} switched to manual mode")
            # Notify all registered callbacks
            for callback in self.manual_mode_callbacks:
                await callback(new_record)

    def _handle_message_update_wrapper(self, payload: Dict[str, Any]):
        """Wrapper for handling message updates that creates a task"""
        asyncio.create_task(self._handle_message_update(payload))

    async def _handle_message_update(self, payload: Dict[str, Any]):
        """Handle message updates"""
        logger.info(f"Received message update: {payload}")

        # Get the new message record
        new_record = payload.get("data", {}).get("record", {})

        print(new_record)

        issue_id = new_record.get("issue_id")

        if not issue_id:
            logger.error(f"Message update missing issue_id: {payload}")
            return

        # Get the issue to check if it's in manual mode
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"{os.getenv('API_BASE_URL')}/private/issues/{issue_id}"
            )

            if response.status != 200:
                logger.error(f"Failed to get issue {issue_id}: {await response.text()}")
                return

            issue_data = await response.json()

            # Only process messages for manual issues
            if issue_data.get("status") != "manual":
                logger.info(f"Ignoring message for non-manual issue {issue_id}")
                return

        # Process the message
        message = {
            "id": new_record.get("id"),
            "issue_id": issue_id,
            "from_user": new_record.get("from_user"),
            "text": new_record.get("text"),
            "timestamp": new_record.get("timestamp"),
        }

        # Check if it's from admin or user
        if message["from_user"] == "Admin":
            logger.info(f"New admin message in issue {issue_id}")
            # Notify admin message callbacks
            for callback in self.admin_message_callbacks:
                await callback(
                    {
                        "issue_id": issue_id,
                        "telegram_chat_id": issue_data.get("telegram_chat_id"),
                        "message": message,
                    }
                )
        elif message["from_user"] != "GPT":
            logger.info(f"New user message in issue {issue_id}")
            # Notify new message callbacks
            for callback in self.new_message_callbacks:
                await callback({"issue_id": issue_id, "message": message})

    def register_manual_mode_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for manual mode events"""
        self.manual_mode_callbacks.append(callback)

    def register_new_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for new message events"""
        self.new_message_callbacks.append(callback)

    def register_admin_message_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ):
        """Register a callback for admin message events"""
        self.admin_message_callbacks.append(callback)

    async def stop(self):
        """Stop listening for realtime events"""
        logger.info("Stopping realtime event handler...")

        if self.issues_channel:
            await self.issues_channel.unsubscribe()

        if self.messages_channel:
            await self.messages_channel.unsubscribe()

        logger.info("Realtime event handler stopped")


# Singleton instance
realtime_handler = RealtimeHandler()
