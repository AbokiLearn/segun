from pydantic_settings import BaseSettings


TMP_DIR = "/tmp"

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    INFERENCE_URL: str
    ACCESS_TOKEN: str


config = Settings()
