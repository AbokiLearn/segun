from pydantic import BaseModel, Field


class ChatData(BaseModel):
    sender: int
    sent_by: str
    chat_id: int | None = None
    text: str | None = None

    class Config:
        arbitrary_types_allowed = True


class TelegramMessage(BaseModel):
    chat_id: str = Field(..., description="The chat ID (user/group/channel/bot)")
    message: str = Field(..., description="The message to send")


class InviteRequest(BaseModel):
    chat_id: str = Field(..., description="The chat ID (group/channel)")
    user_id: str = Field(..., description="The user ID to invite")
    message: str = Field(..., description="The message to send")


class APIResponse(BaseModel):
    data: dict | None = None
    error: str | None = None
    message: str | None = None
