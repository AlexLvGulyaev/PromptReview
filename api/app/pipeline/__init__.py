"""
Prompt Review Pipeline — внутренний движок анализа промптов.

Архитектурно выделен для возможности будущего выноса в отдельный LangChain Service API.

Конвейер:
1. collect_metrics — инструментальный расчёт метрик
2. classify_prompt — классификация через LLM
3. review_prompt — анализ качества через LLM
4. rewrite_prompt — улучшение редакции через LLM
5. compose_result / compose_not_prompt — формирование JSON-ответа
"""

from .prompts import (
    CLASSIFIER_PROMPT,
    CLASSIFIER_FORMAT_INSTRUCTIONS,
    REVIEW_PROMPT,
    REVIEW_FORMAT_INSTRUCTIONS,
    REWRITER_PROMPT,
    REWRITER_FORMAT_INSTRUCTIONS,
)
from .metrics import collect_metrics
from .classifier import classify_prompt, ClassificationResult
from .reviewer import review_prompt, ReviewResult
from .rewriter import rewrite_prompt
from .composer import compose_result, compose_not_prompt
from .pipeline import PromptReviewPipeline

# PromptMetrics импортируется из schemas, не из pipeline
from ..schemas import PromptMetrics

__all__ = [
    # Prompts
    "CLASSIFIER_PROMPT",
    "CLASSIFIER_FORMAT_INSTRUCTIONS",
    "REVIEW_PROMPT",
    "REVIEW_FORMAT_INSTRUCTIONS",
    "REWRITER_PROMPT",
    "REWRITER_FORMAT_INSTRUCTIONS",
    # Components
    "collect_metrics",
    "PromptMetrics",  # из schemas
    "classify_prompt",
    "ClassificationResult",
    "review_prompt",
    "ReviewResult",
    "rewrite_prompt",
    "compose_result",
    "compose_not_prompt",
    # Pipeline
    "PromptReviewPipeline",
]