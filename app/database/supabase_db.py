import time
import uuid
from typing import List, Optional, Dict, Any
from supabase import create_client
from models.issue import Issue, IssueStatus, IssueWithMessages, Message
from models.admin import Admin
from models.faq import FAQ


class SupabaseDB:
    def __init__(self, url: str, key: str):
        self.client = create_client(url, key)

        # Tables
        self.issues_table = "issues"
        self.messages_table = "messages"
        self.admins_table = "admins"
        self.faq_embeddings_table = "faq_embeddings"

    # Issue methods
    async def get_open_issue_by_chat_id(self, telegram_chat_id: str) -> Optional[Issue]:
        response = (
            self.client.table(self.issues_table)
            .select("*")
            .eq("telegram_chat_id", telegram_chat_id)
            .neq("status", "closed")
            .execute()
        )

        if response.data and len(response.data) > 0:
            issue_data = response.data[0]
            issue_data["id"] = issue_data["id"]
            return Issue(**issue_data)

        return None

    async def create_issue(self, telegram_chat_id: str, username: str) -> Issue:
        current_time = int(time.time())
        issue_id = str(uuid.uuid4())

        issue_data = {
            "id": issue_id,
            "telegram_chat_id": telegram_chat_id,
            "username": username,
            "status": IssueStatus.OPEN,
        }

        response = self.client.table(
            self.issues_table).insert(issue_data).execute()

        if response.data and len(response.data) > 0:
            return Issue(**response.data[0])

        # Fallback to the data we tried to insert
        return Issue(**issue_data)

    async def get_issue_by_id(self, issue_id: str) -> Optional[Issue]:
        response = (
            self.client.table(self.issues_table)
            .select("*")
            .eq("id", issue_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return Issue(**response.data[0])

        return None

    async def add_message_to_issue(
        self, issue_id: str, from_user: str, text: str
    ) -> Optional[Message]:
        # First get the issue
        issue = await self.get_issue_by_id(issue_id)
        if not issue:
            return None

        current_time = int(time.time())
        message_data = {
            "issue_id": issue_id,
            "from_user": from_user,
            "text": text,
            "timestamp": current_time,
        }

        # Insert the new message into the messages table
        response = self.client.table(
            self.messages_table).insert(message_data).execute()

        if response.data and len(response.data) > 0:
            return Message(**response.data[0])

        return None

    async def update_issue_status(
        self, issue_id: str, status: IssueStatus
    ) -> Optional[Issue]:
        response = (
            self.client.table(self.issues_table)
            .update(
                {
                    "status": status,
                }
            )
            .eq("id", issue_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return Issue(**response.data[0])

        return None

    async def get_all_issues(self) -> List[Issue]:
        response = self.client.table(self.issues_table).select("*").execute()

        if response.data:
            return [Issue(**item) for item in response.data]

        return []

    # Admin methods
    async def get_admin_by_chat_id(self, telegram_chat_id: str) -> Optional[Admin]:
        response = (
            self.client.table(self.admins_table)
            .select("*")
            .eq("telegram_chat_id", telegram_chat_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return Admin(**response.data[0])

        return None

    async def get_all_admins(self) -> List[Admin]:
        """Get all registered admins"""
        response = self.client.table(self.admins_table).select("*").execute()

        if response.data:
            return [Admin(**item) for item in response.data]

        return []

    async def create_admin(self, telegram_chat_id: str, username: str) -> Admin:
        admin_id = str(uuid.uuid4())

        admin_data = {
            "id": admin_id,
            "telegram_chat_id": telegram_chat_id,
            "username": username,
        }

        response = self.client.table(
            self.admins_table).insert(admin_data).execute()

        if response.data and len(response.data) > 0:
            return Admin(**response.data[0])

        # Fallback to the data we tried to insert
        return Admin(**admin_data)

    # FAQ methods
    async def get_all_faqs(self) -> List[FAQ]:
        response = self.client.table(
            self.faq_embeddings_table).select("*").execute()

        if response.data:
            return [FAQ(**item) for item in response.data]

        return []

    async def create_faq(
        self, question: str, answer: str, embedding: Optional[list] = None
    ) -> FAQ:
        # Store in the embeddings table
        embedding_data = {
            "question": question,
            "answer": answer,
            "embedding": embedding or [],  # Use empty list if no embedding provided
        }

        response = (
            self.client.table(self.faq_embeddings_table)
            .insert(embedding_data)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FAQ(**response.data[0])

        # Fallback to the data we tried to insert
        return FAQ(**embedding_data)

    async def get_faq_by_id(self, faq_id: str) -> Optional[FAQ]:
        response = (
            self.client.table(self.faq_embeddings_table)
            .select("*")
            .eq("id", faq_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FAQ(**response.data[0])

        return None

    async def update_faq(
        self, faq_id: str, question: str, answer: str, embedding: Optional[list] = None
    ) -> Optional[FAQ]:
        # Update FAQ in the embeddings table
        update_data = {"question": question, "answer": answer}

        # Add embedding to update if provided
        if embedding:
            update_data["embedding"] = embedding

        response = (
            self.client.table(self.faq_embeddings_table)
            .update(update_data)
            .eq("id", faq_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return FAQ(**response.data[0])

        return None

    async def delete_faq(self, faq_id: str) -> bool:
        # Delete from embeddings table
        response = (
            self.client.table(self.faq_embeddings_table)
            .delete()
            .eq("id", faq_id)
            .execute()
        )

        return response.data is not None and len(response.data) > 0

    async def search_similar_questions(
        self, query_embedding: List[float], match_threshold: float = 0.7, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar questions using vector similarity"""
        # Using cosine distance to find similar embeddings
        result = self.client.rpc(
            "match_faq_embeddings",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": limit,
            },
        ).execute()

        return result.data if result.data else []

    async def get_issue_messages(self, issue_id: str) -> IssueWithMessages:
        # First check if issue exists
        issue = await self.get_issue_by_id(issue_id)
        if not issue:
            return None

        # Get messages for this issue
        response = (
            self.client.table(self.messages_table)
            .select("*")
            .eq("issue_id", issue_id)
            .order("timestamp")
            .execute()
        )

        messages = []
        if response.data:
            messages = [Message(**msg) for msg in response.data]

        return IssueWithMessages(issue_id=issue_id, messages=messages)
