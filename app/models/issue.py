from email import message
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class IssueStatus(str, Enum):
    OPEN = "open"
    MANUAL = "manual"
    CLOSED = "closed"


class Message(BaseModel):
    id: Optional[str] = None
    issue_id: str
    from_user: str
    text: str
    timestamp: int


class Issue(BaseModel):
    id: str
    telegram_chat_id: str
    username: str
    status: IssueStatus


class IssueCreate(BaseModel):
    telegram_chat_id: str
    username: str


class IssueResponse(BaseModel):
    issue_id: str
    status: str


class MessageCreate(BaseModel):
    message: str


class MessageResponse(BaseModel):
    id: str
    issue_id: str
    from_user: str
    text: str
    timestamp: int


class IssueWithMessages(BaseModel):
    issue_id: str
    messages: List[Message]
