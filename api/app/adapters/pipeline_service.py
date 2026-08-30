"""
Pipeline Service Adapter для Prompt Review Service.

Вызывает вынесенный Pipeline Service через HTTP API
(BACKEND_TYPE=langchain_service). JSON-контракт идентичен
in-process режиму: PromptReviewRequest → PromptReviewResponse.
"""

import httpx

from ..schemas import PromptReviewRequest, PromptReviewResponse
from ..logger import get_logger
from .base import BackendAdapter

logger = get_logger(__name__)


class PipelineServiceAdapter(BackendAdapter):
    """
    Адаптер для вызова вынесенного Pipeline Service через HTTP API.

    Используется при BACKEND_TYPE=langchain_service. LLM-вызовы выполняются
    в отдельном процессе/контейнере (pipeline_service), API-слой остаётся
    тонким шлюзом. Конфигурация через переменные окружения:
    - PIPELINE_SERVICE_URL (например, http://pipeline-service:8001)
    """

    def __init__(self, url: str, timeout: int = 30):
        """
        Инициализация адаптера.

        Args:
            url: Базовый URL Pipeline Service (например, http://localhost:8001)
            timeout: Timeout запроса в секундах
        """
        self.url = url.rstrip("/")
        # Запас поверх таймаута пайплайна: LLM-бюджет считается внутри
        # сервиса, HTTP-обвязка не должна срезать его раньше времени
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def review(self, request: PromptReviewRequest) -> PromptReviewResponse:
        """
        Выполнить анализ промпта через Pipeline Service.

        Args:
            request: Запрос на анализ

        Returns:
            PromptReviewResponse: Результат анализа
        """
        try:
            response = await self.client.post(
                f"{self.url}/process",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return PromptReviewResponse.model_validate(response.json())
        except httpx.TimeoutException as e:
            raise RuntimeError(f"Pipeline Service timeout after {self.timeout}s: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Pipeline Service returned HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"Pipeline Service unavailable: {e}")

    async def health_check(self) -> bool:
        """
        Проверить доступность Pipeline Service.

        Returns:
            bool: True если сервис отвечает на /health
        """
        try:
            response = await self.client.get(f"{self.url}/health")
            return response.status_code == 200
        except httpx.HTTPError as e:
            logger.warning(f"Pipeline Service health check failed: {e}")
            return False

    async def close(self):
        """Закрыть HTTP-клиент."""
        await self.client.aclose()