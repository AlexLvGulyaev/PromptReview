"""
Форматирование ответов Prompt Review Service для Telegram.

Преобразует JSON-ответ от FastAPI в читаемое сообщение с HTML форматированием.
"""

from typing import Dict, Any, List, Optional
from html import escape as html_escape


def format_prompt_response(data: Dict[str, Any]) -> str:
    """
    Форматирование ответа для промпта (is_prompt=true).

    Args:
        data: JSON-ответ от API

    Returns:
        str: Форматированное сообщение для Telegram (HTML)
    """
    sections = []

    # Заголовок с качеством
    quality_level = data.get('quality_level', 'not_applicable')

    # Маппинг качества на русский язык
    quality_text = {
        'excellent': 'Отлично',
        'good': 'Хорошо',
        'fair': 'Удовлетворительно',
        'poor': 'Плохо',
        'not_applicable': 'Не применимо'
    }

    # Маппинг эмодзи
    quality_emoji = {
        'excellent': '🌟',
        'good': '✅',
        'fair': '⚠️',
        'poor': '❌',
        'not_applicable': '❓'
    }

    text = quality_text.get(quality_level, 'Неизвестно')
    emoji = quality_emoji.get(quality_level, '📊')

    sections.append(f"<b>{emoji} Качество: {text}</b>")
    sections.append("")

    # Назначение (экранируем HTML)
    purpose = data.get('purpose')
    if purpose:
        sections.append("<b>🎯 Назначение:</b>")
        sections.append(html_escape(purpose))
        sections.append("")

    # Метрики (числа не требуют экранирования)
    metrics = data.get('metrics', {})
    if metrics:
        sections.append("<b>📊 Метрики:</b>")
        chars = metrics.get('characters', 0)
        words = metrics.get('words', 0)
        lines = metrics.get('lines', 0)
        sections.append(f"Символов: {chars} • Слов: {words} • Строк: {lines}")
        sections.append("")

    # Оценки
    scores = data.get('scores')
    if scores:
        sections.append("<b>📈 Оценки (1–10):</b>")

        # Критерии для отображения
        criteria_map = {
            'clarity': ('Понятность', scores.get('clarity', 0)),
            'completeness': ('Полнота', scores.get('completeness', 0)),
            'ambiguity_absence': ('Отсутствие неоднозначностей', scores.get('ambiguity_absence', 0)),
            'target_audience_fit': ('Соответствие аудитории', scores.get('target_audience_fit', 0)),
            'output_format': ('Формат результата', scores.get('output_format', 0)),
            'constraints_quality': ('Качество ограничений', scores.get('constraints_quality', 0)),
            'missing_assumptions': ('Достаточность предположений', scores.get('missing_assumptions', 0)),
            'structure_reusability': ('Структурированность', scores.get('structure_reusability', 0)),
        }

        for key, (name, value) in criteria_map.items():
            # Визуальная шкала
            filled = int(value)
            empty = 10 - filled
            bar = '█' * filled + '░' * empty
            sections.append(f"{name}: {bar} {value}/10")

        # Общая оценка
        overall = scores.get('overall', 0)
        sections.append(f"<b>Общая оценка:</b> {overall:.1f}/10")
        sections.append("")

    # Сильные стороны (экранируем HTML)
    strengths = data.get('strengths', [])
    if strengths:
        sections.append("<b>✅ Сильные стороны:</b>")
        for strength in strengths:
            sections.append(f"• {html_escape(strength)}")
        sections.append("")

    # Слабые стороны (экранируем HTML)
    weaknesses = data.get('weaknesses', [])
    if weaknesses:
        sections.append("<b>⚠️ Слабые стороны:</b>")
        for weakness in weaknesses:
            sections.append(f"• {html_escape(weakness)}")
        sections.append("")

    # Рекомендации (экранируем текст)
    recommendations = data.get('recommendations', [])
    if recommendations:
        sections.append("<b>💡 Рекомендации:</b>")
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            text = rec.get('text', '')

            # Эмодзи для приоритета
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }
            emoji = priority_emoji.get(priority, '⚪')

            sections.append(f"{emoji} {html_escape(text)}")
        sections.append("")

    # Улучшенная редакция (в кодовом блоке - экранируем HTML)
    revised_prompt = data.get('revised_prompt')
    if revised_prompt:
        sections.append("<b>📝 Улучшенная редакция:</b>")
        sections.append("<pre>")
        sections.append(html_escape(revised_prompt))
        sections.append("</pre>")
        sections.append("")

    # Время обработки
    processing_time = data.get('processing_time_ms', 0)
    sections.append(f"<i>Время обработки: {processing_time} мс</i>")

    return '\n'.join(sections)


def format_not_prompt_response(data: Dict[str, Any]) -> str:
    """
    Форматирование ответа для обычного текста (is_prompt=false).

    Args:
        data: JSON-ответ от API

    Returns:
        str: Форматированное сообщение для Telegram (HTML)
    """
    sections = []

    # Заголовок
    sections.append("<b>❓ Текст не распознан как промпт</b>")
    sections.append("")

    # Причина (экранируем HTML)
    reason = data.get('reason')
    if reason:
        sections.append("<b>🔍 Причина:</b>")
        sections.append(html_escape(reason))
        sections.append("")

    # Метрики (числа не требуют экранирования)
    metrics = data.get('metrics', {})
    if metrics:
        sections.append("<b>📊 Метрики:</b>")
        chars = metrics.get('characters', 0)
        words = metrics.get('words', 0)
        lines = metrics.get('lines', 0)
        sections.append(f"Символов: {chars} • Слов: {words} • Строк: {lines}")
        sections.append("")

    # Варианты преобразования (экранируем HTML)
    conversion_options = data.get('conversion_options', [])
    if conversion_options:
        sections.append("<b>🔄 Варианты преобразования в промпт:</b>")
        for i, option in enumerate(conversion_options, 1):
            sections.append(f"{i}. {html_escape(option)}")
        sections.append("")

    # Время обработки
    processing_time = data.get('processing_time_ms', 0)
    sections.append(f"<i>Время обработки: {processing_time} мс</i>")

    return '\n'.join(sections)


def format_error_response(error_type: str, message: str) -> str:
    """
    Форматирование сообщения об ошибке.

    Args:
        error_type: Тип ошибки
        message: Сообщение об ошибке

    Returns:
        str: Форматированное сообщение для Telegram (HTML)
    """
    sections = []

    # Заголовок
    sections.append("<b>⚠️ Ошибка</b>")
    sections.append("")

    # Тип ошибки
    error_messages = {
        'api_unavailable': 'Сервис анализа временно недоступен. Попробуйте позже.',
        'timeout': 'Превышено время ожидания ответа. Попробуйте отправить более короткий текст.',
        'invalid_response': 'Получен некорректный ответ от сервера.',
        'network_error': 'Ошибка сети. Проверьте подключение к интернету.',
        'unknown': 'Произошла неизвестная ошибка. Попробуйте позже.',
    }

    user_message = error_messages.get(error_type, html_escape(message))
    sections.append(user_message)
    sections.append("")
    sections.append("<i>Попробуйте отправить текст ещё раз или обратитесь в поддержку.</i>")

    return '\n'.join(sections)


def format_response(data: Dict[str, Any]) -> str:
    """
    Универсальное форматирование ответа API.

    Автоматически выбирает форматтер на основе is_prompt.

    Args:
        data: JSON-ответ от API или данные об ошибке

    Returns:
        str: Форматированное сообщение для Telegram (HTML)
    """
    # Проверяем, это ответ API или ошибка
    if 'error' in data:
        # Это ошибка
        return format_error_response(
            data.get('error', 'unknown'),
            data.get('message', 'Неизвестная ошибка')
        )

    # Это нормальный ответ API
    is_prompt = data.get('is_prompt', False)

    if is_prompt:
        return format_prompt_response(data)
    else:
        return format_not_prompt_response(data)