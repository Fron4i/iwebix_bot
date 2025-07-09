from pydantic import BaseSettings

class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения (.env)."""

    bot_token: str
    database_url: str = "postgresql://postgres:postgres@localhost:5432/iwebix_bot"
    owner_username: str = "iwebix_man"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 