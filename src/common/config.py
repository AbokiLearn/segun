from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOGFIRE_TOKEN: str
    MONGO_DB: str
    MONGO_URI: str
    OPENAI_API_KEY: str
    TELEGRAM_TOKEN: str


settings = Settings()
