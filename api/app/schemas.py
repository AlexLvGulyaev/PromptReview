"""
Pydantic-модели для Prompt Review Service API.

Соответствуют JSON-контракту, зафиксированному в SPEC.md и PEl05.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class QualityLevel(str, Enum):
    """Уровень качества промпта."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NOT_APPLICABLE = "not_applicable"


class Source(str, Enum):
    """Источник запроса."""
    WEB = "web"
    TELEGRAM = "telegram"
    N8N = "n8n"
    CLI = "cli"


class ReviewMode(str, Enum):
    """Режим анализа."""
    STANDARD = "standard"
    DETAILED = "detailed"


# ============================================================================
# METRICS (соответствует PEl05)
# ============================================================================

class PromptMetrics(BaseModel):
    """Метрики промпта, рассчитываемые инструментально."""
    characters: int = Field(..., description="Количество символов")
    words: int = Field(..., description="Количество слов")
    lines: int = Field(..., description="Количество строк")
    non_empty_lines: int = Field(..., description="Количество непустых строк")
    markdown_headings: int = Field(default=0, description="Количество заголовков markdown")
    bullet_items: int = Field(default=0, description="Количество маркированных списков")
    numbered_items: int = Field(default=0, description="Количество нумерованных списков")
    markdown_table_lines: int = Field(default=0, description="Количество строк таблиц")
    xml_tags: int = Field(default=0, description="Количество XML-тегов")
    code_blocks: int = Field(default=0, description="Количество блоков кода")
    max_line_length: int = Field(default=0, description="Максимальная длина строки")
    avg_line_length: int = Field(default=0, description="Средняя длина строки")


# ============================================================================
# SCORES (соответствует PEl05)
# ============================================================================

class PromptScores(BaseModel):
    """Оценки качества промпта по критериям."""
    clarity: int = Field(..., ge=0, le=10, description="Понятность постановки задачи")
    completeness: int = Field(..., ge=0, le=10, description="Полнота требований")
    ambiguity_absence: int = Field(..., ge=0, le=10, description="Отсутствие неоднозначностей")
    target_audience_fit: int = Field(..., ge=0, le=10, description="Соответствие целевой аудитории")
    output_format: int = Field(..., ge=0, le=10, description="Формат ожидаемого результата")
    constraints_quality: int = Field(..., ge=0, le=10, description="Качество ограничений")
    missing_assumptions: int = Field(..., ge=0, le=10, description="Наличие недостающих предположений")
    structure_reusability: int = Field(..., ge=0, le=10, description="Структурированность и воспроизводимость")
    overall: float = Field(..., ge=0, le=10, description="Интегральная оценка")


# ============================================================================
# RECOMMENDATION
# ============================================================================

class Recommendation(BaseModel):
    """Рекомендация по улучшению промпта."""
    priority: str = Field(..., pattern="^(high|medium|low)$", description="Приоритет: high, medium, low")
    text: str = Field(..., description="Текст рекомендации")


# ============================================================================
# REQUEST
# ============================================================================

class PromptReviewRequest(BaseModel):
    """Запрос на анализ промпта."""
    prompt_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Текст для анализа"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        description="Идентификатор пользователя (для истории, аналитики, лимитов)"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Идентификатор запроса (автогенерация, если не указан)"
    )
    source: Source = Field(
        default=Source.WEB,
        description="Источник запроса: web, telegram, n8n, cli"
    )
    review_mode: ReviewMode = Field(
        default=ReviewMode.STANDARD,
        description="Режим анализа: standard или detailed"
    )


# ============================================================================
# RESPONSE
# ============================================================================

class PromptReviewResponse(BaseModel):
    """Ответ на анализ промпта.

    Соответствует JSON-контракту из PEl05 и SPEC.md.
    """
    request_id: str = Field(..., description="Идентификатор запроса")
    user_id: str = Field(..., description="Идентификатор пользователя")
    is_prompt: bool = Field(..., description="Является ли текст промптом")

    # Поля для is_prompt=true
    purpose: Optional[str] = Field(
        default=None,
        description="Назначение промпта (только если is_prompt=true)"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Сильные стороны промпта"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Слабые стороны промпта"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Рекомендации по улучшению"
    )
    scores: Optional[PromptScores] = Field(
        default=None,
        description="Оценки по критериям (только если is_prompt=true)"
    )
    quality_level: QualityLevel = Field(
        ...,
        description="Уровень качества: excellent, good, fair, poor, not_applicable"
    )
    revised_prompt: Optional[str] = Field(
        default=None,
        description="Улучшенная редакция промпта (только если is_prompt=true)"
    )

    # Поля для is_prompt=false
    reason: Optional[str] = Field(
        default=None,
        description="Причина, почему текст не является промптом (только если is_prompt=false)"
    )
    conversion_options: List[str] = Field(
        default_factory=list,
        description="Варианты преобразования в промпт (только если is_prompt=false)"
    )

    # Общие поля
    metrics: PromptMetrics = Field(..., description="Метрики текста")
    processing_time_ms: int = Field(..., description="Время обработки в миллисекундах")
    notes: List[str] = Field(
        default_factory=list,
        description="Дополнительные заметки"
    )


# ============================================================================
# ERROR RESPONSE
# ============================================================================

class ErrorResponse(BaseModel):
    """Ошибка API."""
    error: str = Field(..., description="Код ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    details: dict = Field(default_factory=dict, description="Дополнительные детали")


# ============================================================================
# HEALTH CHECK
# ============================================================================

class HealthResponse(BaseModel):
    """Ответ health check."""
    status: str = Field(..., description="Статус: ok или error")
    backend: Optional[str] = Field(default=None, description="Тип backend")
    backend_available: Optional[bool] = Field(default=None, description="Доступность backend")