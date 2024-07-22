from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
)
import logfire

from common.commands import (
    start,
    handle_message,
    register_user,
    receive_phone,
    cancel_registration,
    RegistrationStates,
    unknown,
)
from common.bot import get_application
from common.config import settings

logfire.configure(token=settings.LOGFIRE_TOKEN)


def main():
    app = get_application()

    start_handler = CommandHandler("start", start)
    app.add_handler(start_handler)

    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(message_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_user)],
        states={
            RegistrationStates.PHONE: [MessageHandler(filters.CONTACT, receive_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
    app.add_handler(conv_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    app.add_handler(unknown_handler)

    with logfire.span("running bot"):
        app.run_polling()


if __name__ == "__main__":
    main()
