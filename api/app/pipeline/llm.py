"""
Фабрика LLM для Prompt Review Pipeline.

Конфигурация LLM принадлежит пайплайну: она используется как in-process
(LangChainAdapter), так и вынесенным Pipeline Service (pipeline_service/).

Поддерживаемые провайдеры:
- OpenAI (через OPENAI_API_KEY)
- Ollama (локальные модели)
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)


def create_llm(
    model: str,
    timeout: int,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseChatModel:
    """
    Создать LLM instance по конфигурации.

    Args:
        model: Модель для LangChain (openai, ollama)
        timeout: Timeout запроса в секундах
        api_key: API ключ (для OpenAI)
        base_url: Base URL (для Ollama)

    Returns:
        BaseChatModel: LangChain Chat Model
    """
    if model == "openai":
        from langchain_openai import ChatOpenAI

        api_key = api_key or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI model. "
                "Set it in environment or pass api_key parameter."
            )

        retry_attempts = max(0, settings.RETRY_MAX_ATTEMPTS)
        # Бюджет REQUEST_TIMEOUT_SECONDS распределяется на все попытки:
        # суммарное время LLM-вызова не превышает общий таймаут запроса
        if retry_attempts:
            attempt_timeout = max(5, timeout // (retry_attempts + 1))
        else:
            attempt_timeout = timeout
        logger.info(
            "LLM retry configuration",
            extra={
                "backend": "langchain",
                "retry_max_attempts": retry_attempts,
                "request_timeout": timeout,
                "attempt_timeout": attempt_timeout,
            }
        )

        return ChatOpenAI(
            api_key=api_key,
            model=settings.OPENAI_MODEL,  # Configurable model
            temperature=0,
            timeout=attempt_timeout,
            max_retries=retry_attempts,
        )

    elif model == "ollama":
        from langchain_ollama import ChatOllama

        base_url = base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434"
        ollama_model = settings.OLLAMA_MODEL or "gemma2:9b"

        return ChatOllama(
            model=ollama_model,
            base_url=base_url,
            temperature=0,
        )

    else:
        raise ValueError(
            f"Unknown model: {model}. Supported: openai, ollama"
        )