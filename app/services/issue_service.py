from typing import List, Optional, Dict, Any
import time
from models.issue import Issue, IssueStatus, IssueWithMessages, Message, MessageResponse
from database.supabase_db import SupabaseDB
from services.openai_service import OpenAIService


class IssueService:
    def __init__(self, supabase_db: SupabaseDB, openai_service: OpenAIService):
        self.supabase_db = supabase_db
        self.openai_service = openai_service

    async def get_open_issue(self, telegram_chat_id: str) -> Optional[Issue]:
        return await self.supabase_db.get_open_issue_by_chat_id(telegram_chat_id)

    async def create_issue(self, telegram_chat_id: str, username: str) -> Issue:
        return await self.supabase_db.create_issue(telegram_chat_id, username)

    async def get_issue(self, issue_id: str) -> Optional[Issue]:
        return await self.supabase_db.get_issue_by_id(issue_id)

    async def get_messages(self, issue_id: str) -> IssueWithMessages:
        return await self.supabase_db.get_issue_messages(issue_id)

    async def add_user_message(
        self, issue_id: str, username: str, message_text: str
    ) -> Optional[MessageResponse]:
        issue = await self.supabase_db.get_issue_by_id(issue_id)

        print(issue, username, message_text)

        if not issue or issue.status == IssueStatus.CLOSED:
            return None

        # Add user message to the issue
        await self.supabase_db.add_message_to_issue(issue_id, username, message_text)

        # If issue is in manual mode, don't generate automatic response
        if issue.status == IssueStatus.MANUAL:
            return None

        # Generate embedding for the user message
        message_embedding = await self.openai_service.generate_embedding(message_text)

        # Search for relevant FAQ entries
        similar_faqs = await self.supabase_db.search_similar_questions(
            message_embedding
        )

        # Get all messages for this issue to provide context
        issue_with_messages = await self.supabase_db.get_issue_messages(issue_id)
        messages = issue_with_messages.messages

        # Generate AI response
        ai_response = await self.openai_service.generate_response(
            messages=messages, faq_context=similar_faqs
        )

        # Add AI response to the issue
        ai_message = await self.supabase_db.add_message_to_issue(
            issue_id, "GPT", ai_response
        )

        return ai_message

    async def add_admin_message(
        self, issue_id: str, admin_username: str, message_text: str
    ) -> Optional[Message]:
        issue = await self.supabase_db.get_issue_by_id(issue_id)

        if not issue:
            return None

        # If issue is in automatic mode, switch to manual
        if issue.status == IssueStatus.OPEN:
            await self.supabase_db.update_issue_status(issue_id, IssueStatus.MANUAL)

        # Add admin message to the issue
        return await self.supabase_db.add_message_to_issue(
            issue_id, "Admin", message_text
        )

    async def switch_to_manual(self, issue_id: str) -> Optional[Issue]:
        issue = await self.supabase_db.get_issue_by_id(issue_id)

        if not issue or issue.status != IssueStatus.OPEN:
            return None

        return await self.supabase_db.update_issue_status(issue_id, IssueStatus.MANUAL)

    async def close_issue(self, issue_id: str) -> Optional[Issue]:
        issue = await self.supabase_db.get_issue_by_id(issue_id)

        if not issue or issue.status == IssueStatus.CLOSED:
            return None

        return await self.supabase_db.update_issue_status(issue_id, IssueStatus.CLOSED)

    async def get_all_issues(self) -> List[Issue]:
        return await self.supabase_db.get_all_issues()

    async def get_manual_issues(self) -> List[Issue]:
        """Get all issues in manual mode"""
        all_issues = await self.supabase_db.get_all_issues()
        return [issue for issue in all_issues if issue.status == IssueStatus.MANUAL]
