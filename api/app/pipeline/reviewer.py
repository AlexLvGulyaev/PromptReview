"""
Анализ качества промпта.

Вызывает LLM для оценки промпта по критериям (PEl05 approach).
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from .prompts import REVIEW_PROMPT, REVIEW_FORMAT_INSTRUCTIONS
from .metrics import PromptMetrics
from .classifier import parse_json_response
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class Recommendation:
    """Рекомендация по улучшению промпта."""

    priority: str  # high, medium, low
    text: str

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        return {
            "priority": self.priority,
            "text": self.text,
        }


@dataclass
class PromptScores:
    """Оценки качества промпта по критериям."""

    clarity: int
    completeness: int
    ambiguity_absence: int
    target_audience_fit: int
    output_format: int
    constraints_quality: int
    missing_assumptions: int
    structure_reusability: int
    overall: float

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        return {
            "clarity": self.clarity,
            "completeness": self.completeness,
            "ambiguity_absence": self.ambiguity_absence,
            "target_audience_fit": self.target_audience_fit,
            "output_format": self.output_format,
            "constraints_quality": self.constraints_quality,
            "missing_assumptions": self.missing_assumptions,
            "structure_reusability": self.structure_reusability,
            "overall": self.overall,
        }


@dataclass
class ReviewResult:
    """Результат анализа качества промпта."""

    purpose: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[Recommendation]
    scores: PromptScores
    quality_level: str  # excellent, good, acceptable, weak, unusable

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        return {
            "purpose": self.purpose,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "scores": self.scores.to_dict(),
            "quality_level": self.quality_level,
        }


async def review_prompt(
    llm: BaseChatModel,
    prompt_text: str,
    metrics: PromptMetrics,
) -> ReviewResult:
    """
    Проанализировать качество промпта.

    Вызывает LLM с REVIEW_PROMPT.

    Args:
        llm: LangChain Chat Model
        prompt_text: Текст промпта
        metrics: Метрики промпта

    Returns:
        ReviewResult: Результат анализа
    """
    prompt = ChatPromptTemplate.from_template(REVIEW_PROMPT)
    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "prompt_text": prompt_text,
            "metrics": json.dumps(metrics.model_dump(), ensure_ascii=False, indent=2),
            "format_instructions": REVIEW_FORMAT_INSTRUCTIONS,
        })

        # Парсим JSON-ответ
        content = response.content if hasattr(response, "content") else str(response)
        result = parse_json_response(content)

        # Парсим рекомендации
        recommendations_raw = result.get("recommendations", [])
        recommendations = []
        for r in recommendations_raw:
            if isinstance(r, dict):
                recommendations.append(Recommendation(
                    priority=r.get("priority", "medium"),
                    text=r.get("text", ""),
                ))
            elif isinstance(r, str):
                recommendations.append(Recommendation(
                    priority="medium",
                    text=r,
                ))

        # Парсим оценки
        scores_raw = result.get("scores", {})
        scores = PromptScores(
            clarity=scores_raw.get("clarity", 0),
            completeness=scores_raw.get("completeness", 0),
            ambiguity_absence=scores_raw.get("ambiguity_absence", 0),
            target_audience_fit=scores_raw.get("target_audience_fit", 0),
            output_format=scores_raw.get("output_format", 0),
            constraints_quality=scores_raw.get("constraints_quality", 0),
            missing_assumptions=scores_raw.get("missing_assumptions", 0),
            structure_reusability=scores_raw.get("structure_reusability", 0),
            overall=scores_raw.get("overall", 0),
        )

        # Определяем quality_level
        quality_level = result.get("quality_level", "good").lower()

        return ReviewResult(
            purpose=result.get("purpose", "Анализ промпта"),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            recommendations=recommendations,
            scores=scores,
            quality_level=quality_level,
        )

    except Exception as e:
        logger.warning(f"LLM review failed, using heuristic fallback: {e}")
        # Fallback на эвристику
        return review_prompt_heuristic(prompt_text, metrics)


def review_prompt_heuristic(prompt_text: str, metrics: PromptMetrics) -> ReviewResult:
    """
    Эвристический анализ качества промпта (fallback).

    Используется при недоступности LLM.
    """
    strengths = []
    weaknesses = []
    recommendations = []

    # Оценка на основе метрик
    if metrics.characters > 100:
        strengths.append("Достаточный объём промпта")
    else:
        weaknesses.append("Слишком короткий промпт")
        recommendations.append(Recommendation(
            priority="high",
            text="Увеличьте объём промпта, добавив больше деталей",
        ))

    if metrics.markdown_headings > 0:
        strengths.append("Наличие структуры (заголовки)")
    else:
        recommendations.append(Recommendation(
            priority="medium",
            text="Добавьте заголовки для лучшей структуры",
        ))

    if metrics.bullet_items > 2:
        strengths.append("Использование маркированных списков")

    if metrics.code_blocks > 0:
        strengths.append("Наличие примеров кода")

    # Базовые рекомендации
    recommendations.append(Recommendation(
        priority="medium",
        text="Убедитесь, что ролевая инструкция чётко определена",
    ))

    # Расчёт оценок (эвристика)
    clarity = min(10, max(0, 8 if metrics.characters > 50 else 5))
    completeness = min(10, max(0, 7 if metrics.bullet_items > 0 else 4))
    ambiguity_absence = 7
    target_audience_fit = 7
    output_format = min(10, max(0, 6 if metrics.markdown_headings > 0 else 4))
    constraints_quality = 6
    missing_assumptions = 5
    structure_reusability = min(10, max(0, 7 if metrics.markdown_headings > 0 else 5))
    overall = (clarity + completeness + ambiguity_absence + target_audience_fit +
               output_format + constraints_quality + missing_assumptions + structure_reusability) / 8

    # Определение quality_level
    if overall >= 8:
        quality_level = "excellent"
    elif overall >= 6:
        quality_level = "good"
    elif overall >= 4:
        quality_level = "acceptable"
    else:
        quality_level = "weak"

    scores = PromptScores(
        clarity=clarity,
        completeness=completeness,
        ambiguity_absence=ambiguity_absence,
        target_audience_fit=target_audience_fit,
        output_format=output_format,
        constraints_quality=constraints_quality,
        missing_assumptions=missing_assumptions,
        structure_reusability=structure_reusability,
        overall=round(overall, 1),
    )

    return ReviewResult(
        purpose="Анализ на основе метрик (LLM недоступен)",
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        scores=scores,
        quality_level=quality_level,
    )