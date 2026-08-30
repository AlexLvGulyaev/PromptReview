"""
Улучшение редакции промпта.

Вызывает LLM для создания улучшенной версии промпта (PEl05 approach).
"""

from typing import Any, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from .prompts import REWRITER_PROMPT, REWRITER_FORMAT_INSTRUCTIONS
from .reviewer import ReviewResult
from .classifier import parse_json_response
from ..logger import get_logger

logger = get_logger(__name__)


async def rewrite_prompt(
    llm: BaseChatModel,
    prompt_text: str,
    review_result: ReviewResult,
    callbacks: Optional[List[Any]] = None,
) -> Optional[str]:
    """
    Создать улучшенную редакцию промпта.

    Вызывает LLM с REWRITER_PROMPT.

    Args:
        llm: LangChain Chat Model
        prompt_text: Исходный текст промпта
        review_result: Результат анализа качества
        callbacks: Callback-обработчики LangChain (например,
            UsageMetadataCallbackHandler для учёта токенов)

    Returns:
        Optional[str]: Улучшенная редакция промпта или None при ошибке
    """
    prompt = ChatPromptTemplate.from_template(REWRITER_PROMPT)
    chain = prompt | llm

    config = {"callbacks": callbacks} if callbacks else None

    try:
        # Формируем списки для промпта
        weaknesses_text = "\n".join(f"- {w}" for w in review_result.weaknesses)
        recommendations_text = "\n".join(f"- {r.text}" for r in review_result.recommendations)

        response = await chain.ainvoke(
            {
                "prompt_text": prompt_text,
                "weaknesses": weaknesses_text,
                "recommendations": recommendations_text,
                "format_instructions": REWRITER_FORMAT_INSTRUCTIONS,
            },
            config=config,
        )

        # Парсим JSON-ответ
        content = response.content if hasattr(response, "content") else str(response)
        result = parse_json_response(content)

        return result.get("revised_prompt")

    except Exception as e:
        logger.warning(f"LLM rewrite failed: {e}")
        return None