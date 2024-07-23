from pydantic import BaseModel, Field


class TelegramMessage(BaseModel):
    chat_id: str = Field(..., description="The chat ID (user/group/channel/bot)")
    message: str = Field(..., description="The message to send")


class InviteRequest(BaseModel):
    user_id: str = Field(..., description="The user ID to invite")
    chat_id: str = Field(..., description="The chat ID (group/channel)")
    message: str = Field(..., description="The message to send")


class APIResponse(BaseModel):
    data: dict | None = None
    error: str | None = None
    message: str | None = None
