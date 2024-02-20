from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    OPENAI_API_KEY: str
    MONGO_URI: str


config = Settings()
