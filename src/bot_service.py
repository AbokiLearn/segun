from telegram.ext import CommandHandler, ConversationHandler, filters, MessageHandler

from time import strftime

from common.commands import (
    cancel_registration,
    handle_message,
    help,
    receive_phone,
    register_user,
    start,
    unknown,
    RegistrationStates,
)
from common.logging import get_bot_logger
from common.bot import get_application

logger = get_bot_logger()


def main():
    app = get_application()

    start_handler = CommandHandler("start", start)
    app.add_handler(start_handler)

    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(message_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_user)],
        states={
            RegistrationStates.PHONE: [MessageHandler(filters.CONTACT, receive_phone)]
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
    app.add_handler(conv_handler)

    help_handler = CommandHandler("help", help)
    app.add_handler(help_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    app.add_handler(unknown_handler)

    start_time = strftime("%Y%m%d_%H:%M:%S")
    with logger.span(f"bot started at {start_time}"):
        app.run_polling()
        end_time = strftime("%Y%m%d_%H:%M:%S")
        logger.info(f"bot stopped at {end_time}")


if __name__ == "__main__":
    main()