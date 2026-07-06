"""
Абстрактный интерфейс Backend-адаптера.

FastAPI не содержит бизнес-логику Prompt Review.
Вся работа с Prompt Review Engine выполняется через BackendAdapter.
"""

from abc import ABC, abstractmethod
from ..schemas import PromptReviewRequest, PromptReviewResponse


class BackendAdapter(ABC):
    """
    Абстрактный интерфейс для взаимодействия с Prompt Review Engine.

    Реализации:
    - LangFlowAdapter — HTTP Request к LangFlow API
    - LangChainAdapter — Прямой вызов LangChain pipeline
    """

    @abstractmethod
    async def review(self, request: PromptReviewRequest) -> PromptReviewResponse:
        """
        Выполнить анализ промпта.

        Args:
            request: Запрос на анализ промпта

        Returns:
            PromptReviewResponse: Результат анализа
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Проверить доступность backend.

        Returns:
            bool: True если backend доступен, False иначе
        """
        pass