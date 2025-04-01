from typing import Optional, List
from models.admin import Admin
from database.supabase_db import SupabaseDB


class AdminService:
    def __init__(self, supabase_db: SupabaseDB):
        self.supabase_db = supabase_db

    async def get_admin_by_chat_id(self, telegram_chat_id: str) -> Optional[Admin]:
        return await self.supabase_db.get_admin_by_chat_id(telegram_chat_id)

    async def get_all_admins(self) -> List[Admin]:
        return await self.supabase_db.get_all_admins()

    async def create_admin(
        self, telegram_chat_id: str, username: str
    ) -> Optional[Admin]:
        # Check if admin already exists
        existing_admin = await self.supabase_db.get_admin_by_chat_id(telegram_chat_id)
        if existing_admin:
            return None

        # Create new admin
        return await self.supabase_db.create_admin(telegram_chat_id, username)
