from pydantic import BaseModel


class Admin(BaseModel):
    id: str
    telegram_chat_id: str
    username: str


class AdminCreate(BaseModel):
    telegram_chat_id: str
    username: str
