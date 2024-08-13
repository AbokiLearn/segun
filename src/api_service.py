from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import asyncio

from common.schema import TelegramMessage, InviteBatch, APIResponse
from common.logging import get_api_logger
from common.config import settings
from common.bot import get_bot


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

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


@app.post("/send-invites", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def send_invites(invite_batch: InviteBatch, api_key: str = Depends(get_api_key)):
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENCY)

    async def process_invite(invite):
        async with semaphore:
            try:
                chat_invite_link = await bot.create_chat_invite_link(
                    chat_id=invite.chat_id
                )
                invite_message = f"{invite.message}\n\nJoin the group: {chat_invite_link.invite_link}"
                tasks = [
                    bot.send_message(chat_id=user_id, text=invite_message)
                    for user_id in invite.user_ids
                ]
                await asyncio.gather(*tasks)
                return {"status": "success", "chat_id": invite.chat_id}
            except Exception as e:
                logger.error(
                    "Error sending invite: {error=}",
                    error=str(e),
                    user_ids=invite.user_ids,
                    chat_id=invite.chat_id,
                )
                raise {"status": "error", "chat_id": invite.chat_id, "error": str(e)}

    try:
        results = await asyncio.gather(
            *[process_invite(invite) for invite in invite_batch.invites]
        )
        successful = [res for res in results if res["status"] == "success"]
        failed = [res for res in results if res["status"] == "error"]

        return {
            "message": f"Processed {len(successful)} invites successfully, {len(failed)} failed.",
            "data": {"successful": successful, "failed": failed},
        }
    except Exception as e:
        logger.error("Error sending invites: {error=}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        await bot.send_message(chat_id=invite.user_id, text="Invite has failed please refer to the website and follow the instructions or contact us at wazobiacode@gmail.com")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}
