from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_DOMAIN: str
    API_KEY: str
    BOT_AT: str
    BOT_URL: str
    LOGFIRE_LEVEL: str
    LOGFIRE_TOKEN: str
    MONGO_DB: str
    MONGO_URI: str
    OPENAI_API_KEY: str
    TELEGRAM_TOKEN: str


settings = Settings()
