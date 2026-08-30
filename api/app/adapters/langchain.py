"""
LangChain Adapter для Prompt Review Service.

Выполняет LangChain pipeline через PromptReviewPipeline.
Использует LLM для классификации, анализа и улучшения промптов.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel

from ..schemas import PromptReviewRequest, PromptReviewResponse
from ..pipeline import PromptReviewPipeline
from ..pipeline.llm import create_llm
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

        Конфигурация LLM (retry, таймаут-бюджет, провайдер) вынесена в
        api/app/pipeline/llm.py и переиспользуется Pipeline Service.

        Returns:
            BaseChatModel: LangChain Chat Model
        """
        if self._llm is None:
            self._llm = create_llm(
                model=self.model,
                timeout=self.timeout,
                api_key=self.api_key,
                base_url=self.base_url,
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