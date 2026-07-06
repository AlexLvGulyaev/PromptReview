import re
import json

from langchain_core.tools import tool


@tool
def prompt_metrics(prompt: str) -> str:
    """
    Вычисляет объективные характеристики промпта:
    размер, количество слов, строк, заголовков, списков, таблиц,
    XML-разделителей и кодовых блоков.
    Используется перед анализом качества промпта.
    """
    lines = prompt.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    words = re.findall(r"\b[\wА-Яа-яЁё-]+\b", prompt)

    markdown_headings = [
        line for line in lines
        if line.strip().startswith("#")
    ]

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

    xml_tags = re.findall(r"</?[A-Za-z_][A-Za-z0-9_-]*>", prompt)

    code_blocks = re.findall(r"```", prompt)

    max_line_length = max((len(line) for line in lines), default=0)
    avg_line_length = round(
        sum(len(line) for line in non_empty_lines) / len(non_empty_lines),
        1
    ) if non_empty_lines else 0

    return json.dumps(
    {
        "characters": len(prompt),
        "words": len(words),
        "lines": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "markdown_headings": len(markdown_headings),
        "bullet_items": len(bullet_items),
        "numbered_items": len(numbered_items),
        "markdown_table_lines": len(markdown_tables),
        "xml_tags": len(xml_tags),
        "code_blocks": len(code_blocks) // 2,
        "max_line_length": max_line_length,
        "avg_line_length": avg_line_length,
    },
    ensure_ascii=False,
    indent=2,
)