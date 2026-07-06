"""
Инструментальный расчёт метрик промпта.

Перенесено из PEl05 (n8n/langchain/prompt-review-langchain-code.js)
и PEl04 (langchain/tools/prompt_metrics.py).
"""

import re

# Импортируем Pydantic-модель из schemas для согласованности
from ..schemas import PromptMetrics


def collect_metrics(text: str) -> PromptMetrics:
    """
    Рассчитать объективные характеристики промпта.

    Соответствует collectPromptMetrics из PEl05.

    Args:
        text: Текст промпта

    Returns:
        PromptMetrics: Рассчитанные метрики
    """
    lines = text.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]

    # Подсчёт слов (включая русские)
    words = re.findall(r"\b[\wА-Яа-яЁё-]+\b", text)

    # Markdown-элементы
    markdown_headings = [line for line in lines if line.strip().startswith("#")]
    bullet_items = [
        line for line in lines
        if re.match(r"^\s*(-|\*|\+)\s+", line)
    ]
    numbered_items = [
        line for line in lines
        if re.match(r"^\s*\d+[\.)]\s+", line)
    ]
    markdown_tables = [
        line for line in lines
        if "|" in line and line.strip().startswith("|")
    ]

    # XML-теги
    xml_tags = re.findall(r"</?[A-Za-z_][A-Za-z0-9_-]*>", text)

    # Блоки кода
    code_block_markers = re.findall(r"```", text)

    # Длины строк
    max_line_length = max((len(line) for line in lines), default=0)
    avg_line_length = (
        int(sum(len(line) for line in non_empty_lines) / len(non_empty_lines))
        if non_empty_lines
        else 0
    )

    return PromptMetrics(
        characters=len(text),
        words=len(words),
        lines=len(lines),
        non_empty_lines=len(non_empty_lines),
        markdown_headings=len(markdown_headings),
        bullet_items=len(bullet_items),
        numbered_items=len(numbered_items),
        markdown_table_lines=len(markdown_tables),
        xml_tags=len(xml_tags),
        code_blocks=len(code_block_markers) // 2,
        max_line_length=max_line_length,
        avg_line_length=avg_line_length,
    )