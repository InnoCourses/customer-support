from typing import List, Optional, Dict, Any
from models.faq import FAQ
from database.supabase_db import SupabaseDB
from services.openai_service import OpenAIService


class FAQService:
    def __init__(self, supabase_db: SupabaseDB, openai_service: OpenAIService):
        self.supabase_db = supabase_db
        self.openai_service = openai_service

    async def get_all_faqs(self) -> List[FAQ]:
        return await self.supabase_db.get_all_faqs()

    async def create_faq(self, question: str, answer: str) -> Optional[FAQ]:
        # Generate embedding for the question
        embedding = await self.openai_service.generate_embedding(question)

        # Create FAQ in Supabase
        faq = await self.supabase_db.create_faq(question, answer, embedding)

        return faq

    async def get_faq(self, faq_id: str) -> Optional[FAQ]:
        return await self.supabase_db.get_faq_by_id(faq_id)

    async def update_faq(
        self, faq_id: str, question: str, answer: str
    ) -> Optional[FAQ]:
        # Check if FAQ exists
        existing_faq = await self.supabase_db.get_faq_by_id(faq_id)
        if not existing_faq:
            return None

        # Generate new embedding for the updated question
        embedding = await self.openai_service.generate_embedding(question)

        # Update FAQ in Supabase
        updated_faq = await self.supabase_db.update_faq(
            faq_id, question, answer, embedding
        )

        return updated_faq

    async def delete_faq(self, faq_id: str) -> bool:
        # Check if FAQ exists
        existing_faq = await self.supabase_db.get_faq_by_id(faq_id)
        if not existing_faq:
            return False

        # Delete from Supabase
        return await self.supabase_db.delete_faq(faq_id)
