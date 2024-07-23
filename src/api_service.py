from fastapi import FastAPI, HTTPException, status

from common.schema import TelegramMessage, InviteRequest, APIResponse
from common.logging import get_api_logger
from common.bot import get_bot


app = FastAPI()
bot = get_bot()
logger = get_api_logger(app)


@app.post("/send_message", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def send_message(message: TelegramMessage):
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
async def send_invite(invite: InviteRequest):
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
