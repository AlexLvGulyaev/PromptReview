"""
Формирование итогового JSON-ответа.

Соответствует composeResult и composeNotPrompt из PEl05.
"""

from typing import List, Optional

from ..schemas import (
    PromptReviewResponse,
    PromptScores,
    QualityLevel,
    Recommendation,
)
from .metrics import PromptMetrics
from .classifier import ClassificationResult
from .reviewer import ReviewResult


def compose_result(
    request_id: str,
    user_id: str,
    metrics: PromptMetrics,
    review_result: ReviewResult,
    revised_prompt: Optional[str],
    processing_time_ms: int,
) -> PromptReviewResponse:
    """
    Сформировать ответ для промпта (is_prompt=true).

    Соответствует composeResult из PEl05.

    Args:
        request_id: ID запроса
        user_id: ID пользователя
        metrics: Метрики промпта
        review_result: Результат анализа
        revised_prompt: Улучшенная редакция
        processing_time_ms: Время обработки

    Returns:
        PromptReviewResponse: Полный JSON-ответ
    """
    # Маппинг quality_level
    quality_level_map = {
        "excellent": QualityLevel.EXCELLENT,
        "good": QualityLevel.GOOD,
        "acceptable": QualityLevel.FAIR,  # backward compatibility
        "fair": QualityLevel.FAIR,
        "weak": QualityLevel.POOR,
        "unusable": QualityLevel.POOR,
    }
    quality_level = quality_level_map.get(
        review_result.quality_level.lower(),
        QualityLevel.GOOD
    )

    # Преобразование scores
    scores = PromptScores(
        clarity=review_result.scores.clarity,
        completeness=review_result.scores.completeness,
        ambiguity_absence=review_result.scores.ambiguity_absence,
        target_audience_fit=review_result.scores.target_audience_fit,
        output_format=review_result.scores.output_format,
        constraints_quality=review_result.scores.constraints_quality,
        missing_assumptions=review_result.scores.missing_assumptions,
        structure_reusability=review_result.scores.structure_reusability,
        overall=review_result.scores.overall,
    )

    return PromptReviewResponse(
        request_id=request_id,
        user_id=user_id,
        is_prompt=True,
        purpose=review_result.purpose,
        strengths=review_result.strengths,
        weaknesses=review_result.weaknesses,
        recommendations=[
            Recommendation(priority=r.priority, text=r.text)
            for r in review_result.recommendations
        ],
        scores=scores,
        quality_level=quality_level,
        revised_prompt=revised_prompt,
        reason=None,
        conversion_options=[],
        metrics=metrics,
        processing_time_ms=processing_time_ms,
    )


def compose_not_prompt(
    request_id: str,
    user_id: str,
    metrics: PromptMetrics,
    classification: ClassificationResult,
    processing_time_ms: int,
) -> PromptReviewResponse:
    """
    Сформировать ответ для не-промпта (is_prompt=false).

    Соответствует composeNotPrompt из PEl05.

    Args:
        request_id: ID запроса
        user_id: ID пользователя
        metrics: Метрики текста
        classification: Результат классификации
        processing_time_ms: Время обработки

    Returns:
        PromptReviewResponse: Полный JSON-ответ
    """
    return PromptReviewResponse(
        request_id=request_id,
        user_id=user_id,
        is_prompt=False,
        purpose=None,
        strengths=[],
        weaknesses=[],
        recommendations=[],
        scores=None,
        quality_level=QualityLevel.NOT_APPLICABLE,
        revised_prompt=None,
        reason=classification.reason,
        conversion_options=[
            "Добавьте ролевую инструкцию (например: \"Ты — ...\")",
            "Укажите ожидаемый формат результата",
            "Опишите конкретную задачу",
        ],
        metrics=metrics,
        processing_time_ms=processing_time_ms,
    )