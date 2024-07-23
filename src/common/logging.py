from fastapi import FastAPI
import logfire

from common.config import settings

logfire.configure(
    token=settings.LOGFIRE_TOKEN,
    console=logfire.ConsoleOptions(min_log_level=settings.LOGFIRE_LEVEL),
)


def _get_logger(tags: list[str] = [], fastapi_app: FastAPI | None = None):
    if fastapi_app:
        logfire.instrument_fastapi(fastapi_app)

    logger = logfire.with_tags(*tags)

    return logger


def get_api_logger(fastapi_app: FastAPI):
    return _get_logger(["bot-api"], fastapi_app)


def get_bot_logger():
    return _get_logger(["bot"])
