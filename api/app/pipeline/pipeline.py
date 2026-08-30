"""
Prompt Review Pipeline — внутренний движок анализа промптов.

Архитектурно выделен для возможности будущего выноса в отдельный LangChain Service API.

Конвейер:
1. collect_metrics — инструментальный расчёт метрик
2. classify_prompt — классификация через LLM
3. review_prompt — анализ качества через LLM (если is_prompt=true)
4. rewrite_prompt — улучшение редакции через LLM (если is_prompt=true)
5. compose_result / compose_not_prompt — формирование JSON-ответа
"""

import time
import uuid
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import UsageMetadataCallbackHandler

from ..schemas import PromptReviewRequest, PromptReviewResponse, TokenUsage
from .metrics import collect_metrics
from .classifier import classify_prompt, ClassificationResult
from .reviewer import review_prompt, ReviewResult
from .rewriter import rewrite_prompt
from .composer import compose_result, compose_not_prompt
from ..logger import get_logger

logger = get_logger(__name__)


def _summarize_usage(callback: UsageMetadataCallbackHandler) -> Optional[TokenUsage]:
    """Суммировать usage_metadata по всем LLM-вызовам запроса.

    Args:
        callback: заполненный UsageMetadataCallbackHandler

    Returns:
        TokenUsage или None, если провайдер не отдал данных о токенах.
    """
    usage_by_model = callback.usage_metadata or {}
    if not usage_by_model:
        return None

    summary = TokenUsage()
    for model_usage in usage_by_model.values():
        summary.input_tokens += model_usage.get("input_tokens", 0)
        summary.output_tokens += model_usage.get("output_tokens", 0)
        summary.total_tokens += model_usage.get("total_tokens", 0)

    if summary.total_tokens == 0:
        return None
    return summary


class PromptReviewPipeline:
    """
    Конвейер анализа промптов.

    Может быть использован напрямую или через LangChainAdapter.
    Архитектурно готов к выносу в отдельный сервис.
    """

    def __init__(self, llm: BaseChatModel, use_heuristic_fallback: bool = True):
        """
        Инициализация конвейера.

        Args:
            llm: LangChain Chat Model (ChatOpenAI, ChatOllama, etc.)
            use_heuristic_fallback: Использовать эвристику при недоступности LLM
        """
        self.llm = llm
        self.use_heuristic_fallback = use_heuristic_fallback

    async def process(self, request: PromptReviewRequest) -> PromptReviewResponse:
        """
        Выполнить полный цикл анализа промпта.

        Args:
            request: Запрос на анализ

        Returns:
            PromptReviewResponse: Результат анализа
        """
        start_time = time.time()
        request_id = request.request_id or f"req_{int(start_time * 1000)}_{uuid.uuid4().hex[:8]}"

        logger.info(
            f"Processing prompt review request",
            extra={
                "request_id": request_id,
                "user_id": request.user_id,
                "prompt_length": len(request.prompt_text),
            }
        )

        try:
            # Callback учёта токенов на все LLM-вызоры запроса
            usage_callback = UsageMetadataCallbackHandler()
            llm_callbacks = [usage_callback]

            # Этап 1: Сбор метрик
            metrics = collect_metrics(request.prompt_text)
            logger.debug(
                f"Metrics collected",
                extra={
                    "request_id": request_id,
                    "characters": metrics.characters,
                    "words": metrics.words,
                }
            )

            # Этап 2: Классификация
            classification = await classify_prompt(
                self.llm,
                request.prompt_text,
                callbacks=llm_callbacks,
            )
            logger.info(
                f"Classification completed",
                extra={
                    "request_id": request_id,
                    "is_prompt": classification.is_prompt,
                    "confidence": classification.confidence,
                }
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Если текст не является промптом
            if not classification.is_prompt:
                response = compose_not_prompt(
                    request_id=request_id,
                    user_id=request.user_id,
                    metrics=metrics,
                    classification=classification,
                    processing_time_ms=processing_time_ms,
                )
                response.token_usage = _summarize_usage(usage_callback)
                _log_usage(request_id, response.token_usage)
                return response

            # Этап 3: Анализ качества
            review_result = await review_prompt(
                self.llm,
                request.prompt_text,
                metrics,
                callbacks=llm_callbacks,
            )
            logger.info(
                f"Review completed",
                extra={
                    "request_id": request_id,
                    "quality_level": review_result.quality_level,
                    "overall_score": review_result.scores.overall,
                }
            )

            # Этап 4: Улучшенная редакция
            revised_prompt = await rewrite_prompt(
                self.llm,
                request.prompt_text,
                review_result,
                callbacks=llm_callbacks,
            )
            if revised_prompt:
                logger.debug(
                    f"Prompt rewritten",
                    extra={"request_id": request_id}
                )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Этап 5: Формирование результата
            response = compose_result(
                request_id=request_id,
                user_id=request.user_id,
                metrics=metrics,
                review_result=review_result,
                revised_prompt=revised_prompt,
                processing_time_ms=processing_time_ms,
            )
            response.token_usage = _summarize_usage(usage_callback)

            logger.info(
                f"Prompt review completed",
                extra={
                    "request_id": request_id,
                    "is_prompt": True,
                    "quality_level": response.quality_level.value,
                    "processing_time_ms": processing_time_ms,
                    **_usage_log_fields(response.token_usage),
                }
            )

            return response

        except Exception as e:
            logger.exception(
                f"Prompt review failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                }
            )
            raise


def _usage_log_fields(token_usage: Optional[TokenUsage]) -> dict:
    """Поля токенов для extra-словаря структурного лога."""
    if token_usage is None:
        return {}
    return {
        "tokens_input": token_usage.input_tokens,
        "tokens_output": token_usage.output_tokens,
        "tokens_total": token_usage.total_tokens,
    }


def _log_usage(request_id: str, token_usage: Optional[TokenUsage]) -> None:
    """Залогировать учёт токенов (ветка is_prompt=false)."""
    if token_usage is None:
        return
    logger.info(
        "LLM token usage",
        extra={"request_id": request_id, **_usage_log_fields(token_usage)},
    )