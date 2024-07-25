from enum import Enum

from telegram import (
    Chat,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User,
)
from telegram import error as tg_error
from telegram.ext import ContextTypes, ConversationHandler

from common import web_client
from common.config import settings
from common.logging import bot_logger
from common.schema import ChatData


def _get_chat_data(update: Update) -> ChatData:
    sender = update.effective_sender

    if isinstance(sender, User):
        sent_by = "user"
    elif isinstance(sender, Chat):
        sent_by = "channel"
    else:
        sent_by = "unknown"

    return ChatData(
        sender=sender.id,
        sent_by=sent_by,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        text=update.effective_message.text if update.effective_message else None,
    )


# ---[General Commands]-------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    bot_logger.debug(
        "Bot started: {sender=}",
        sender=chat_data.sender,
        sent_by=chat_data.sent_by,
        chat_id=chat_data.chat_id,
    )
    await context.bot.send_message(
        chat_id=chat_data.chat_id,
        text="Welcome to the WazobiaCode Bootcamp Bot! I'm here to assist you with your registration and provide access to course materials. To get started, use /register to link your Telegram account. If you need any help, just type /help for a list of available commands.",
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

    bot_logger.debug(
        "Help command requested: {sender=}",
        sender=chat_data.sender,
        sent_by=chat_data.sent_by,
        chat_id=chat_data.chat_id,
    )
    await context.bot.send_message(chat_id=chat_data.chat_id, text=help_text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = _get_chat_data(update)

    bot_logger.debug(
        "Unknown command: {text=}",
        text=chat_data.text,
        sender=chat_data.sender,
        sent_by=chat_data.sent_by,
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

    try:
        bot_logger.debug(
            "Sending registration message: {sender=}",
            sender=chat_data.sender,
            sent_by=chat_data.sent_by,
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
            bot_logger.error(
                "Error responding to registration command: {error=}",
                error=str(e),
                sender=chat_data.sender,
                sent_by=chat_data.sent_by,
                chat_id=chat_data.chat_id,
            )

    return RegistrationStates.PHONE


async def receive_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    chat_data = _get_chat_data(update)
    phone_number = update.message.contact.phone_number

    await update.message.reply_text("Thank you! Please wait...")

    res = await web_client.register_user(phone_number, chat_data.sender)

    if res.error:
        await update.message.reply_text(
            f"An error occurred while registering your telegram account: {res.error}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    bot_logger.debug(
        "Received phone number: {sender=}",
        phone_number=phone_number,
        sender=chat_data.sender,
        sent_by=chat_data.sent_by,
        chat_id=chat_data.chat_id,
    )
    await update.message.reply_text(res.message, reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def cancel_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    chat_data = _get_chat_data(update)

    bot_logger.debug(
        "Cancelling registration: {sender=}",
        sender=chat_data.sender,
        sent_by=chat_data.sent_by,
        chat_id=chat_data.chat_id,
    )
    await update.message.reply_text(
        "Registration cancelled. You can start over by using the /register command.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
