from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    database_url: str
    api_key: str
    extraction_model: str = "minimax/minimax-m3:free"
    classification_model: str = "minimax/minimax-m3:free"


@lru_cache
def get_settings() -> Settings:
    return Settings()
