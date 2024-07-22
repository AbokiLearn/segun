from fastapi import FastAPI, HTTPException
import logfire

from common.schema import TelegramMessage
from common.bot import get_application
from common.config import settings


app = FastAPI()
tg = get_application()

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_fastapi(app)


@app.post("/send_message")
async def send_message(message: TelegramMessage):
    try:
        await tg.bot.send_message(chat_id=message.chat_id, text=message.message)
        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        logfire.error("Error sending message: {error=}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_service:app", host="0.0.0.0", port=8000, reload=True)
