from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from common.schema import TelegramMessage, InviteRequest, APIResponse
from common.logging import get_api_logger
from common.config import settings
from common.bot import get_bot


app = FastAPI()
bot = get_bot()
logger = get_api_logger(app)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == settings.API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@app.post("/send-message", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def send_message(message: TelegramMessage, api_key: str = Depends(get_api_key)):
    try:
        logger.info(
            "Sending message to {chat_id=}",
            chat_id=message.chat_id,
            message=message.message,
        )
        await bot.send_message(chat_id=message.chat_id, text=message.message)
        return {"data": {"message": "Message sent successfully"}}
    except Exception as e:
        logger.error("Error sending message: {error=}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.post("/send-invite", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def send_invite(invite: InviteRequest, api_key: str = Depends(get_api_key)):
    try:
        chat_invite_link = await bot.create_chat_invite_link(chat_id=invite.chat_id)
        invite_message = (
            f"{invite.message}\n\nJoin the group: {chat_invite_link.invite_link}"
        )
        await bot.send_message(chat_id=invite.user_id, text=invite_message)
        return {"status": "success", "message": "Invite sent successfully"}
    except Exception as e:
        logger.error("Error sending invite: {error=}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
