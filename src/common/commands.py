from telegram.ext import ContextTypes, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import error as tg_error

from dataclasses import dataclass
from enum import Enum

from common.logging import get_bot_logger
from common.config import settings

logger = get_bot_logger()


@dataclass
class ChatData:
    user_id: int
    chat_id: int
    text: str | None = None


def _get_chat_data(update: Update) -> ChatData:
    return ChatData(
        user_id=update.effective_user.id if update.effective_user else None,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        text=update.effective_message.text if update.effective_message else None,
    )


# ---[General Commands]-------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    logger.debug(
        "Bot started: {user_id=}", user_id=chat_data.user_id, chat_id=chat_data.chat_id
    )
    await context.bot.send_message(chat_id=chat_data.chat_id, text="Hello, I'm a bot!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    logger.debug(
        "Received message: {text=}",
        text=chat_data.text,
        user_id=chat_data.user_id,
        chat_id=chat_data.chat_id,
    )
    await context.bot.send_message(
        chat_id=chat_data.chat_id, text=f"you said: '{chat_data.text}'"
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/register - Register your Telegram account

For any issues or questions, please contact support.
    """

    logger.debug(
        "Help command requested: {user_id=}",
        user_id=chat_data.user_id,
        chat_id=chat_data.chat_id,
    )
    await context.bot.send_message(chat_id=chat_data.chat_id, text=help_text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    logger.debug(
        "Unknown command: {text=}",
        text=chat_data.text,
        user_id=chat_data.user_id,
        chat_id=chat_data.chat_id,
    )
    await context.bot.send_message(
        chat_id=chat_data.chat_id,
        text="Sorry, I don't know that command. Use /help to see a list of available commands.",
    )


# ---[Registration Commands]-------------------------------------------------------


class RegistrationStates(Enum):
    PHONE = 0


async def register_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    chat_data = _get_chat_data(update)

    keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # TODO: need to talk to website API, handle errors, already registered, etc.

    try:
        logger.debug(
            "Sending registration message: {user_id=}",
            user_id=chat_data.user_id,
            chat_id=chat_data.chat_id,
        )
        await update.message.reply_text(
            """\
Welcome to the WazobiaCode Bootcamp!
To register your telegram account with us, please share your phone number. This will allow us to verify your identity and enable access to the course material.
            """,
            reply_markup=reply_markup,
        )
    except tg_error.BadRequest as e:
        if e.message == "Phone number can be requested in private chats only":
            await update.message.reply_text(
                f"""\
Registration can only be completed via private chats.
Please reach out to <a href="{settings.BOT_URL}">{settings.BOT_AT}</a>
                """,
                parse_mode="HTML",
            )
        else:
            logger.error(
                "Error responding to registration command: {error=}",
                error=str(e),
                user_id=chat_data.user_id,
                chat_id=chat_data.chat_id,
            )

    return RegistrationStates.PHONE


async def receive_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    user = update.message.from_user
    phone_number = update.message.contact.phone_number

    logger.debug(
        "Received phone number: {user_id=}",
        phone_number=phone_number,
        user_id=user.id,
        chat_id=update.effective_chat.id,
    )
    await update.message.reply_text(
        f"Thank you, {user.full_name}! Your telegram account has been registered successfully."
    )

    return ConversationHandler.END


async def cancel_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    logger.debug(
        "Cancelling registration: {user_id=}",
        user_id=update.message.from_user.id,
        chat_id=update.effective_chat.id,
    )
    await update.message.reply_text(
        "Registration cancelled. You can start over by using the /register command.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
