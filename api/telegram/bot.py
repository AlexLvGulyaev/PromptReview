"""
Telegram Bot для Prompt Review Service.

Архитектура:
    Telegram Bot (UI-слой)
        ↓
    POST /review
        ↓
    FastAPI API
        ↓
    Prompt Review Engine

Бот не содержит бизнес-логику анализа.
Вся логика остаётся в Prompt Review Service.
"""

import os
import sys
import asyncio
import logging
from typing import Optional

import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hide_link
from dotenv import load_dotenv

# Добавляем путь к formatter
sys.path.insert(0, os.path.dirname(__file__))
from formatter import format_response, format_error_response


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Загружаем переменные окружения
# Приоритет: переменные окружения > .env файл
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PROMPT_REVIEW_API_URL = os.getenv('PROMPT_REVIEW_API_URL', 'http://localhost:8000')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '60'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ПРОВЕРКА КОНФИГУРАЦИИ
# ============================================================================

def validate_config():
    """Проверка обязательных переменных окружения."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN не указан. "
            "Установите переменную окружения или добавьте в .env файл."
        )


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================================

validate_config()

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# ============================================================================
# API CLIENT
# ============================================================================

async def call_review_api(text: str, user_id: str) -> dict:
    """
    Вызов FastAPI API для анализа текста.

    Args:
        text: Текст для анализа
        user_id: Идентификатор пользователя Telegram

    Returns:
        dict: JSON-ответ от API

    Raises:
        RuntimeError: При ошибке вызова API
    """
    # Формируем запрос в соответствии с PromptReviewRequest
    payload = {
        "prompt_text": text,
        "user_id": f"telegram:{user_id}",
        "source": "telegram",
        "review_mode": "standard"
    }

    url = f"{PROMPT_REVIEW_API_URL}/review"
    timeout = httpx.Timeout(API_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            logger.error(f"API timeout for user {user_id}")
            return {
                "error": "timeout",
                "message": "Превышено время ожидания ответа от сервера"
            }

        except httpx.ConnectError:
            logger.error(f"API connection error for user {user_id}")
            return {
                "error": "api_unavailable",
                "message": "Сервис анализа недоступен"
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error for user {user_id}: {e}")
            return {
                "error": "http_error",
                "message": f"Ошибка сервера: {e.response.status_code}"
            }

        except Exception as e:
            logger.exception(f"Unexpected API error for user {user_id}: {e}")
            return {
                "error": "unknown",
                "message": "Неизвестная ошибка при обращении к серверу"
            }


# ============================================================================
# HANDLERS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start.

    Приветственное сообщение с описанием возможностей бота.
    """
    user_name = message.from_user.first_name or "Пользователь"

    welcome_text = (
        f"👋 *Привет, {user_name}\\!*\n\n"
        f"*Prompt Review Bot* анализирует качество промптов для AI\\.\n\n"
        f"*Что я умею:*\n"
        f"• Оцениваю понятность и структуру промпта\n"
        f"• Выделяю сильные и слабые стороны\n"
        f"• Даю рекомендации по улучшению\n"
        f"• Предлагаю улучшенную редакцию промпта\n\n"
        f"*Как использовать:*\n"
        f"Просто отправьте мне текст, и я проанализирую, "
        f"является ли он промптом и насколько он хорош\\.\n\n"
        f"_Отправьте промпт или любой текст для анализа\\._"
    )

    await message.answer(welcome_text, parse_mode="MarkdownV2")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.

    Справка по использованию бота.
    """
    help_text = (
        "*📖 Справка по использованию*\n\n"
        "*Команды:*\n"
        "/start — Начать работу с ботом\n"
        "/help — Показать справку\n\n"
        "*Как использовать:*\n"
        "1\\. Отправьте текст или промпт боту\n"
        "2\\. Бот проанализирует текст\n"
        "3\\. Получите результат анализа\n\n"
        "*Что анализируется:*\n"
        "• Понятность постановки задачи\n"
        "• Полнота требований\n"
        "• Отсутствие неоднозначностей\n"
        "• Соответствие целевой аудитории\n"
        "• Формат ожидаемого результата\n"
        "• Качество ограничений\n\n"
        "*Формат ответа:*\n"
        "Если текст — промпт, вы получите:\n"
        "• Оценку качества \\(1–10\\)\n"
        "• Сильные и слабые стороны\n"
        "• Рекомендации по улучшению\n"
        "• Улучшенную редакцию\n\n"
        "Если текст — не промпт, вы получите:\n"
        "• Объяснение причины\n"
        "• Варианты преобразования в промпт\n"
    )

    await message.answer(help_text, parse_mode="MarkdownV2")


@dp.message(F.text)
async def handle_message(message: Message):
    """
    Обработчик текстовых сообщений.

    Анализирует текст через Prompt Review API.
    """
    # Проверяем, что текст не пустой
    if not message.text or len(message.text.strip()) == 0:
        await message.answer(
            "❌ *Пожалуйста, отправьте текст для анализа\\.*",
            parse_mode="MarkdownV2"
        )
        return

    # Проверяем минимальную длину (API требует минимум 10 символов)
    if len(message.text.strip()) < 10:
        await message.answer(
            "⚠️ *Текст слишком короткий\\.*\n\n"
            "Минимальная длина — 10 символов\\. "
            "Пожалуйста, отправьте более длинный текст\\.",
            parse_mode="MarkdownV2"
        )
        return

    # Показываем индикатор "печатает"
    await message.chat.do('typing')

    # Получаем ID пользователя
    user_id = str(message.from_user.id)

    logger.info(f"Processing request from user {user_id}, text length: {len(message.text)}")

    # Вызываем API
    try:
        result = await call_review_api(message.text, user_id)

        # Форматируем ответ
        formatted_response = format_response(result)

        # Отправляем результат (HTML формат)
        await message.answer(
            formatted_response,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        logger.info(f"Successfully processed request for user {user_id}")

    except Exception as e:
        logger.exception(f"Error processing message for user {user_id}: {e}")

        # Форматируем ошибку
        error_response = format_error_response('unknown', str(e))

        await message.answer(
            error_response,
            parse_mode="MarkdownV2"
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@dp.error()
async def error_handler(event: types.ErrorEvent):
    """
    Глобальный обработчик ошибок.
    """
    logger.exception(f"Unhandled error: {event.exception}")

    # Пытаемся отправить сообщение об ошибке пользователю
    if event.update.message:
        try:
            await event.update.message.answer(
                "⚠️ *Произошла ошибка\\.*\n\n"
                "Попробуйте отправить текст ещё раз или обратитесь в поддержку\\.",
                parse_mode="MarkdownV2"
            )
        except Exception:
            pass


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Запуск бота."""
    logger.info(f"Starting Prompt Review Telegram Bot")
    logger.info(f"API URL: {PROMPT_REVIEW_API_URL}")
    logger.info(f"API Timeout: {API_TIMEOUT}s")

    # Проверяем доступность API перед запуском
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get(f"{PROMPT_REVIEW_API_URL}/health")
            if response.status_code == 200:
                health = response.json()
                logger.info(f"API health check: {health}")
            else:
                logger.warning(f"API health check failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Cannot connect to API: {e}")

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        sys.exit(1)