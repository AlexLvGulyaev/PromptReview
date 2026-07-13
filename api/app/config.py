"""
Конфигурация Prompt Review Service API.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Настройки приложения."""

    # Backend configuration
    BACKEND_TYPE: str = "langflow"  # langflow или langchain

    # LangFlow configuration
    LANGFLOW_URL: str = "http://localhost:7860"
    LANGFLOW_FLOW_ID: str = ""
    LANGFLOW_API_KEY: str = ""

    # LangChain configuration
    LANGCHAIN_MODEL: str = "openai"  # openai или ollama
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"  # модель для OpenAI
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma2:9b"

    # API configuration
    API_KEY: str = ""  # Опционально, для аутентификации
    CORS_ORIGINS: str = ""  # Разделённый запятыми список origins

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json или text

    # Limits
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_PROMPT_LENGTH: int = 10000

    @property
    def cors_origins_list(self) -> List[str]:
        """Парсить CORS_ORIGINS как список."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Игнорировать лишние переменные из .env


# Глобальный экземпляр настроек
settings = Settings()