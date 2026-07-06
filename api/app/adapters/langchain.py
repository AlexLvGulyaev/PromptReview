"""
LangChain Adapter для Prompt Review Service.

Выполняет LangChain pipeline через PromptReviewPipeline.
Использует LLM для классификации, анализа и улучшения промптов.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel

from ..schemas import PromptReviewRequest, PromptReviewResponse
from ..pipeline import PromptReviewPipeline
from ..config import settings
from ..logger import get_logger
from .base import BackendAdapter

logger = get_logger(__name__)


class LangChainAdapter(BackendAdapter):
    """
    Адаптер для вызова LangChain pipeline напрямую.

    Использует PromptReviewPipeline для:
    - collect_metrics — инструментальный расчёт метрик
    - classify_prompt — классификация через LLM
    - review_prompt — анализ качества через LLM
    - rewrite_prompt — улучшение редакции через LLM
    - compose_result — формирование JSON-ответа

    Поддерживает модели:
    - OpenAI (через OPENAI_API_KEY)
    - Ollama (локальные модели)

    Конфигурация через переменные окружения:
    - LANGCHAIN_MODEL=openai|ollama
    - OPENAI_API_KEY (для OpenAI)
    - OLLAMA_BASE_URL (для Ollama)
    - OLLAMA_MODEL (для Ollama)
    """

    def __init__(
        self,
        model: str = "openai",
        timeout: int = 30,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Инициализация адаптера.

        Args:
            model: Модель для LangChain (openai, ollama)
            timeout: Timeout запроса в секундах
            api_key: API ключ (для OpenAI)
            base_url: Base URL (для Ollama)
        """
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self.base_url = base_url
        self._llm: Optional[BaseChatModel] = None
        self._pipeline: Optional[PromptReviewPipeline] = None

    def _get_llm(self) -> BaseChatModel:
        """
        Получить или создать LLM instance.

        Returns:
            BaseChatModel: LangChain Chat Model
        """
        if self._llm is not None:
            return self._llm

        # Ленивая инициализация LLM
        if self.model == "openai":
            from langchain_openai import ChatOpenAI

            api_key = self.api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required for OpenAI model. "
                    "Set it in environment or pass api_key parameter."
                )

            self._llm = ChatOpenAI(
                api_key=api_key,
                model="gpt-4o-mini",  # Default model for cost efficiency
                temperature=0,
                timeout=self.timeout,
            )

        elif self.model == "ollama":
            from langchain_ollama import ChatOllama

            base_url = self.base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434"
            ollama_model = settings.OLLAMA_MODEL or "gemma2:9b"

            self._llm = ChatOllama(
                model=ollama_model,
                base_url=base_url,
                temperature=0,
            )

        else:
            raise ValueError(
                f"Unknown model: {self.model}. Supported: openai, ollama"
            )

        return self._llm

    async def review(self, request: PromptReviewRequest) -> PromptReviewResponse:
        """
        Выполнить анализ промпта через LangChain pipeline.

        Args:
            request: Запрос на анализ

        Returns:
            PromptReviewResponse: Результат анализа
        """
        # Ленивая инициализация pipeline
        if self._pipeline is None:
            llm = self._get_llm()
            self._pipeline = PromptReviewPipeline(llm=llm)

        return await self._pipeline.process(request)

    async def health_check(self) -> bool:
        """
        Проверить доступность LangChain.

        Returns:
            bool: True если LangChain работает
        """
        try:
            # Проверяем, что LLM инициализирован
            llm = self._get_llm()

            # Для OpenAI - проверяем API ключ
            if self.model == "openai":
                return bool(self.api_key or settings.OPENAI_API_KEY)

            # Для Ollama - можно сделать лёгкий invoke, но это дорого
            # Возвращаем True, так как Ollama работает локально
            return True

        except Exception as e:
            logger.warning(f"LangChain health check failed: {e}")
            return False

    async def close(self):
        """Закрыть ресурсы (если нужно)."""
        # Для LangChain не требуется явного закрытия
        pass