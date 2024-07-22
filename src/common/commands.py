from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import error as tg_error
import logfire

from enum import Enum


# ---[General Commands]-------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Hello, I'm a bot!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    logfire.info(f"Received message from {chat_id}: '{text}'")
    await context.bot.send_message(chat_id=chat_id, text=f"you said: '{text}'")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Sorry, I don't know that command."
    )


# ---[Registration Commands]-------------------------------------------------------


class RegistrationStates(Enum):
    PHONE = 0


async def register_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    keyboard = [[KeyboardButton("Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    # TODO: need to talk to website API, handle errors, already registered, etc.

    try:
        await update.message.reply_text(
            "Hello! To register, please share your phone number.",
            reply_markup=reply_markup,
        )
    except tg_error.BadRequest as e:
        if e.message == "Phone number can be requested in private chats only":
            await update.message.reply_text(
                "Registration can only be completed via private chats."
            )
        else:
            logfire.error(f"Error sending message: {e}")

    return RegistrationStates.PHONE


async def receive_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    user = update.message.from_user
    phone_number = update.message.contact.phone_number

    await update.message.reply_text(
        f"Thank you, {user.full_name}! Your phone number {phone_number} has been registered."
    )

    return ConversationHandler.END


async def cancel_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> RegistrationStates:
    await update.message.reply_text(
        "Registration cancelled. You can start over by using the /register command.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
