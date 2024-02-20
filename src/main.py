# bot/main.py

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
    ForceReply,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    InlineQueryHandler,
    MessageHandler
)
import asyncio

from loguru import logger
from rich import print, inspect

from pathlib import Path

from settings import config, TMP_DIR
import utils


path = Path(__file__).parent.parent

logger.add(
    sink=path/'logs'/'bot.log',
    format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}",
    colorize=True,
    level="INFO",
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""

    logger.info(f"User {update.effective_user.id} started bot")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello, I'm a bot!",
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    
    logger.info(f"User {update.effective_user.id} sent message: {update.message.text}")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text,
    )


async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages or audio files from user."""
    
    audio_file = update.message.audio or update.message.voice

    if not audio_file:
        return
        
    file_size = audio_file.file_size / 1024 / 1024
    duration = audio_file.duration / 60
    logger.info(
        f"Received audio: '{file_size:.2f} mb'\t'{duration:.2f} minutes'"
    )

    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Let me transcribe that for you! This may take a while..."
    )

    logger.info(f"Downloading voice message from user {update.effective_user.id}")
    file = await audio_file.get_file()
    file_path = await file.download_to_drive(
        custom_path=utils.create_tmpfile(file)
    )
    
    call_id = await utils.submit_transcription_job(file_path)
    logger.info(f"Submitted transcription job for user {update.effective_user.id} with call_id {call_id}")
   
    asyncio.create_task(
        utils.check_job_status(call_id, update.effective_chat.id, message.message_id, context.bot)
    ) 
    

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with caps the user message."""
   
    logger.info(f"User {update.effective_user.id} sent command: {update.message.text}")
    
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text_caps,
    )


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with caps the inline user query."""

    query = update.inline_query.query
    if not query:
        return
    
    logger.info(f"User {update.effective_user.id} sent inline query: {query}")

    results = [
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper()),
        )
    ]
    await context.bot.answer_inline_query(update.inline_query.id, results)


async def transcribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Transcribe audio files from the user"""
    await update.message.reply_text(
        'Please send the audio file you want to transcribe.',
        reply_markup=ForceReply(selective=True),
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with unknown command message."""
    
    logger.info(f"User {update.effective_user.id} sent unknown command: {update.message.text}")
     
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


if __name__ == '__main__':
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    caps_handler = CommandHandler('caps', caps)
    transcribe_handler = CommandHandler('transcribe', transcribe_command)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    audio_handler = MessageHandler(filters.VOICE | filters.AUDIO, audio_handler)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    inline_caps_handler = InlineQueryHandler(inline_caps)

    app.add_handler(start_handler)    
    app.add_handler(echo_handler)
    app.add_handler(transcribe_handler)
    app.add_handler(audio_handler)
    app.add_handler(caps_handler)
    app.add_handler(inline_caps_handler)
    app.add_handler(unknown_handler)  # must be last
   
    logger.info("Bot started") 
    app.run_polling()
    logger.info("Bot stopped. Goodbye!")
