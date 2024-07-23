from fastapi import FastAPI

from common.config import settings


def _get_logger(service_name: str):
    import logfire

    logfire.configure(
        service_name=service_name,
        token=settings.LOGFIRE_TOKEN,
        console=logfire.ConsoleOptions(min_log_level=settings.LOGFIRE_LEVEL),
    )
    return logfire


def get_api_logger(fastapi_app: FastAPI):
    logger = _get_logger("telegram-api")
    logger.instrument_fastapi(fastapi_app)
    return logger


def get_bot_logger():
    return _get_logger("telegram-bot")


bot_logger = get_bot_logger()
