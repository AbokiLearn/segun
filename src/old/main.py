# src/main.py

from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
import asyncio

from loguru import logger

from pathlib import Path

from settings import config
import mongo
import llm

CONFIGURE_ASK, CONFIGURE_CONTENT = range(2)

path = Path(__file__).parent.parent

logger.add(
    sink=path / "logs" / "bot.log",
    format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}",
    colorize=True,
    level="INFO",
)

client, db = mongo.connect()


async def fetch_subjects():
    subjects = await mongo.get_subjects(db)
    return subjects


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""

    logger.info(f"User {update.effective_user.id} started bot")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""\
Hello I'm Aboki, an AI chatbot.

I can answer any questions you have about this course.
""",
    )


async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform RAG to answer user question"""

    global subjects

    logger.info(
        f"User {update.effective_user.id} asked a question. Responding with LLM."
    )
    user_message = " ".join(context.args)

    bot_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Working on it..."
    )

    logger.info("Asking Mixtral")
    _, res_q = await llm.extract_question(user_message)
    _, res_s = await llm.determine_subject(res_q.question)

    context_docs = await mongo.vector_search(
        db,
        query=res_q.question,
        subject_ids=[str(subjects[title.value]) for title in res_s.subjects],
    )

    ai_answer = await llm.answer_question(res_q.question, context_docs)

    answer = f"{ai_answer.answer}\n\n" + "\n".join(
        [f"- {x}" for x in ai_answer.sources]
    )

    await bot_message.edit_text(text=answer)
    await bot_message.chat.set_message_reaction(
        message_id=bot_message.message_id, reaction=ReactionTypeEmoji("👍")
    )


async def configure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.effective_user.first_name or "there"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {user_name}, have you already set up the course on AbokiLearn? (Yes/No)",
    )
    return CONFIGURE_ASK


async def configure_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_response = update.message.text.lower()
    if user_response in ["yes", "y"]:
        keyboard = [
            [
                InlineKeyboardButton(
                    "JavaScript Bootcamp", callback_data="JavaScript Bootcamp"
                )
            ],
            [
                InlineKeyboardButton(
                    "Intro to Chemistry", callback_data="Intro to Chemistry"
                )
            ],
            [InlineKeyboardButton("Mathematics", callback_data="Mathematics")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Which content do you want the bot to have access to?",
            reply_markup=reply_markup,
        )
        return CONFIGURE_CONTENT
    else:
        raise Exception("User has not configured the course in the web app.")


async def configure_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    content_choice = query.data
    await query.edit_message_text(
        text=f"Okay, the bot now has access to your content library: {content_choice}."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Setup was successful!",
    )
    return ConversationHandler.END


async def configure_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Configuration cancelled.",
    )
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with unknown command message."""

    logger.info(
        f"User {update.effective_user.id} sent unknown command: {update.message.text}"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    loop = asyncio.get_event_loop()
    subjects = {
        str(r["title"]): r["_id"] for r in loop.run_until_complete(fetch_subjects())
    }

    start_handler = CommandHandler("start", start)
    question_handler = CommandHandler("question", question)
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("configure", configure)],
        states={
            CONFIGURE_ASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, configure_ask)
            ],
            CONFIGURE_CONTENT: [CallbackQueryHandler(configure_content)],
        },
        fallbacks=[CommandHandler("cancel", configure_cancel)],
    )
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    app.add_handler(start_handler)
    app.add_handler(question_handler)
    app.add_handler(conversation_handler)
    app.add_handler(unknown_handler)  # must be last

    logger.info("Bot started")
    app.run_polling()
    logger.info("Bot stopped. Goodbye!")
