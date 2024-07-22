from telegram.ext import ApplicationBuilder
from common.config import settings

application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()


def get_application():
    return application
