import aiohttp
import logging
from typing import List, Optional, Dict, Any

from models.issue import Issue, IssueResponse, IssueWithMessages, MessageResponse
from models.admin import Admin

logger = logging.getLogger(__name__)


class ApiClient:
    """Client wrapper for the Customer Support API"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _make_request(
        self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the API"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}{endpoint}"
                async with getattr(session, method.lower())(
                    url, json=json_data
                ) as response:
                    if response.status in (200, 201):
                        return await response.json()
                    else:
                        try:
                            error_data = await response.json()
                            error_detail = error_data.get("detail", "Unknown error")
                        except Exception:
                            error_detail = await response.text()
                            logger.error(f"Non-JSON error response: {error_detail}")

                        raise ApiClientError(
                            f"Error {response.status}: {error_detail}",
                            status_code=response.status,
                        )
            except aiohttp.ClientError as e:
                logger.error(f"API request error: {e}")
                raise ApiClientError(f"Connection error: {str(e)}")

    # Public API endpoints (User Bot)

    async def get_user_issue(self, telegram_chat_id: str) -> Optional[IssueResponse]:
        """Get the current open issue for a user"""
        try:
            data = await self._make_request("GET", f"/public/issues/{telegram_chat_id}")
            return IssueResponse(**data)
        except ApiClientError as e:
            if e.status_code == 404:
                return None
            raise

    async def create_issue(self, telegram_chat_id: str, username: str) -> IssueResponse:
        """Create a new issue"""
        data = await self._make_request(
            "POST",
            "/public/issues",
            {"telegram_chat_id": telegram_chat_id, "username": username},
        )
        return IssueResponse(**data)

    async def add_user_message(
        self, issue_id: str, message: str
    ) -> Optional[MessageResponse]:
        """Add a user message to an issue and get AI response"""
        data = await self._make_request(
            "POST", f"/public/issues/{issue_id}/messages", {"message": message}
        )
        if data is None:
            return None
        return MessageResponse(**data)

    async def switch_to_manual(self, issue_id: str) -> IssueResponse:
        """Switch an issue to manual mode"""
        data = await self._make_request("PUT", f"/public/issues/{issue_id}/manual")
        return IssueResponse(**data)

    # Private API endpoints (Admin Bot)

    async def register_admin(self, telegram_chat_id: str, username: str) -> Admin:
        """Register a new admin"""
        data = await self._make_request(
            "POST",
            "/private/admins",
            {"telegram_chat_id": telegram_chat_id, "username": username},
        )
        return Admin(**data)

    async def get_all_admins(self) -> List[Admin]:
        """Get all registered admins"""
        data = await self._make_request("GET", "/private/admins")
        return [Admin(**admin) for admin in data]

    async def get_manual_issues(self) -> List[IssueResponse]:
        """Get all issues in manual mode"""
        data = await self._make_request("GET", "/private/issues/manual")
        return [IssueResponse(**issue) for issue in data]

    async def get_issue(self, issue_id: str) -> Issue:
        """Get a specific issue by ID"""
        data = await self._make_request("GET", f"/private/issues/{issue_id}")
        return Issue(**data)

    async def get_issue_messages(self, issue_id: str) -> IssueWithMessages:
        """Get all messages for an issue"""
        data = await self._make_request("GET", f"/private/issues/{issue_id}/messages")
        return IssueWithMessages(**data)

    async def add_admin_message(self, issue_id: str, message: str) -> Dict[str, Any]:
        """Add an admin message to an issue"""
        data = await self._make_request(
            "POST", f"/private/issues/{issue_id}/messages", {"message": message}
        )
        return data

    async def close_issue(self, issue_id: str) -> Dict[str, Any]:
        """Close an issue"""
        data = await self._make_request("POST", f"/private/issues/{issue_id}/close")
        return data


class ApiClientError(Exception):
    """Exception raised for API client errors"""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
