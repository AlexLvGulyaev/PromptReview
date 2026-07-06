"""
Логирование для Prompt Review Service API.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON-форматтер для структурированного логирования."""

    def format(self, record: logging.LogRecord) -> str:
        """Форматировать лог-запись как JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавляем extra-поля
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "processing_time_ms"):
            log_data["processing_time_ms"] = record.processing_time_ms

        # Добавляем traceback для ошибок
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Текстовый форматтер для разработки."""

    def format(self, record: logging.LogRecord) -> str:
        """Форматировать лог-запись как текст."""
        timestamp = datetime.utcnow().isoformat()
        extra = ""
        if hasattr(record, "request_id"):
            extra += f" [{record.request_id}]"
        if hasattr(record, "user_id"):
            extra += f" user={record.user_id}"

        return f"{timestamp} | {record.levelname:8} | {record.name}{extra} | {record.getMessage()}"


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с настроенным форматтером.

    Args:
        name: Имя логгера

    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Удаляем существующие handlers
    logger.handlers.clear()

    # Создаём handler
    handler = logging.StreamHandler(sys.stdout)

    # Выбираем форматтер
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Глобальный логгер
logger = get_logger("prompt_review")