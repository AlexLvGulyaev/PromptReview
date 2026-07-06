"""
Классификация текста: является ли текст промптом.

Вызывает LLM для классификации (PEl05 approach).
Эвристика доступна как fallback при недоступности LLM.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from .prompts import CLASSIFIER_PROMPT, CLASSIFIER_FORMAT_INSTRUCTIONS
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    """Результат классификации текста."""

    is_prompt: bool
    reason: str
    confidence: float

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        return {
            "is_prompt": self.is_prompt,
            "reason": self.reason,
            "confidence": self.confidence,
        }


def parse_json_response(content: str) -> dict:
    """
    Универсальная функция парсинга JSON-ответа от LLM.

    Удаляет markdown-обёртки и парсит JSON.

    Args:
        content: Текст ответа от LLM

    Returns:
        dict: Распарсенный JSON

    Raises:
        ValueError: Если не удалось распарсить JSON
    """
    # Удаляем markdown-обёртки
    cleaned = content
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nOriginal: {content}")


async def classify_prompt(llm: BaseChatModel, prompt_text: str) -> ClassificationResult:
    """
    Классифицировать текст: является ли он промптом.

    Вызывает LLM с CLASSIFIER_PROMPT.

    Args:
        llm: LangChain Chat Model
        prompt_text: Текст для классификации

    Returns:
        ClassificationResult: Результат классификации
    """
    prompt = ChatPromptTemplate.from_template(CLASSIFIER_PROMPT)
    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "prompt_text": prompt_text,
            "format_instructions": CLASSIFIER_FORMAT_INSTRUCTIONS,
        })

        # Парсим JSON-ответ
        content = response.content if hasattr(response, "content") else str(response)
        result = parse_json_response(content)

        return ClassificationResult(
            is_prompt=result.get("is_prompt", False),
            reason=result.get("reason", "Не удалось определить"),
            confidence=result.get("confidence", 0.5),
        )

    except Exception as e:
        logger.warning(f"LLM classification failed, using fallback: {e}")
        # Fallback на эвристику
        return classify_prompt_heuristic(prompt_text)


def classify_prompt_heuristic(prompt_text: str) -> ClassificationResult:
    """
    Эвристическая классификация текста (fallback).

    Используется при недоступности LLM.

    Признаки промпта:
    - Ролевые инструкции ("Ты —", "Act as", "You are")
    - Описание задачи ("Объясни", "Напиши", "Составь", "Проанализируй")
    - Указание формата ("Ответ должен содержать", "Формат ответа")
    - Условия ("Если", "При условии")
    - Примеры ("Пример:", "Например")
    """
    text_lower = prompt_text.lower()

    # Ролевые инструкции
    role_indicators = [
        "ты —", "ты -", "act as", "you are", "you're a", "ты являешься",
        "представь, что ты", "imagine you are", "твоя роль"
    ]

    # Описание задачи
    task_indicators = [
        "объясни", "напиши", "составь", "проанализируй", "оцени",
        "переведи", "сравни", "опиши", "create", "write", "analyze",
        "explain", "compare", "describe", "evaluate", "translate"
    ]

    # Формат результата
    format_indicators = [
        "ответ должен", "формат ответа", "результат должен содержать",
        "формат результата", "в ответе укажи", "output format",
        "response should", "format:"
    ]

    # Подсчитываем совпадения
    role_count = sum(1 for ind in role_indicators if ind in text_lower)
    task_count = sum(1 for ind in task_indicators if ind in text_lower)
    format_count = sum(1 for ind in format_indicators if ind in text_lower)

    # Проверяем структуру
    lines = prompt_text.split("\n")
    has_structure = (
        any(line.strip().startswith("#") for line in lines) or
        any(line.strip().startswith(("-", "*", "1.")) for line in lines)
    )

    # Эвристика
    is_prompt = False
    reason = "Текст не содержит инструкции для языковой модели"
    confidence = 0.3

    if role_count >= 1 and format_count >= 1:
        is_prompt = True
        reason = "Текст содержит ролевую инструкцию и указание формата результата"
        confidence = 0.8
    elif task_count >= 2:
        is_prompt = True
        reason = "Текст содержит несколько описаний задач"
        confidence = 0.7
    elif role_count >= 1 and task_count >= 1:
        is_prompt = True
        reason = "Текст содержит ролевую инструкцию и описание задачи"
        confidence = 0.75
    elif has_structure and task_count >= 1:
        is_prompt = True
        reason = "Текст структурирован и содержит описание задачи"
        confidence = 0.65

    return ClassificationResult(
        is_prompt=is_prompt,
        reason=reason,
        confidence=confidence,
    )