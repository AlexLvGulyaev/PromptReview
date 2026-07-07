# Задача: создание DEPLOYMENT_GUIDE.md и переработка Quick Start в README

**Дата:** 2026-07-07
**Статус:** В работе

---

## Исходный текст задания

### Контекст

Текущий раздел запуска в README не должен содержать непроверенные команды.

Принято архитектурное решение: README не является источником истины по запуску и развёртыванию проекта. README — публичная витрина и навигатор. Source of Truth по запуску и развёртыванию — docs/DEPLOYMENT_GUIDE.md.

### Что сделать

1. Убрать из README подробный Quick Start с командами установки и запуска.
2. Оставить в README только краткий навигационный раздел.
3. Создать docs/DEPLOYMENT_GUIDE.md.
4. Описать только фактически проверенные сценарии запуска.
5. Не писать команды "на глаз".

### Обязательные сценарии для анализа

Проверить по коду и infra-файлам:
- минимальный локальный запуск FastAPI;
- запуск Web UI;
- запуск LangChain backend;
- запуск LangFlow backend;
- запуск Telegram Bot;
- Docker Compose сценарии;
- какие .env переменные нужны для каждого сценария.

### Главное правило

Если сценарий не проверен или требует дополнительной настройки, он должен быть явно отмечен как "не проверено / требует доработки / отдельный сценарий".

---

## АНАЛИЗ КОДА

### Проверенные сценарии

| Сценарий | Источник в коде | Требования |
|----------|-----------------|------------|
| Локальный FastAPI | `app/main.py`, `config.py` | Python 3.11+, uvicorn, .env |
| Web UI | `app/main.py` lines 85-89 | Автоматически при запуске FastAPI |
| LangChain backend | `adapters/__init__.py`, `config.py` | OPENAI_API_KEY или OLLAMA_BASE_URL |
| Telegram Bot | `telegram/bot.py` | TELEGRAM_BOT_TOKEN, PROMPT_REVIEW_API_URL |
| Docker Compose API | `docker-compose.api.yml` | .env, external network n8n_default |

### Требующие доработки сценарии

| Сценарий | Проблема |
|----------|----------|
| LangFlow backend | Требует развёрнутый LangFlow сервер (не входит в репозиторий) |
| Docker Compose Telegram | Есть Dockerfile, но не проверена интеграция |
| Ollama backend | Требует установленный Ollama на машине |

---

## СТАТУС ЗАДАЧИ

**Текущий статус:** ✅ Завершено (v2.1)

**Выполнено:**
- ✅ Полностью переработан DEPLOYMENT_GUIDE.md (v2.0)
- ✅ Добавлена Model 3: LangFlow Development (v2.1)
- ✅ Добавлены пошаговые инструкции для LangFlow
- ✅ Добавлен импорт Flow из репозитория
- ✅ Обновлена информация о Flow файлах
- ✅ Добавлены troubleshooting для LangFlow
- ✅ Добавлены примеры .env для LangFlow
- ✅ Обновлён README.md

---

## ИСТОЧНИКИ АНАЛИЗА

| Файл | Что проверено |
|------|---------------|
| `api/app/main.py` | Точки входа FastAPI, монтирование Web UI |
| `api/app/config.py` | Переменные окружения, конфигурация |
| `api/app/adapters/__init__.py` | Backend Adapter фабрика |
| `api/telegram/bot.py` | Telegram Bot конфигурация |
| `api/requirements.txt` | Python-зависимости |
| `infra/.env.example` | Пример конфигурации |
| `infra/docker-compose.api.yml` | Docker Compose API |
| `infra/docker-compose.telegram.yml` | Docker Compose Telegram |
| `infra/docker-compose.langflow.yml` | Docker Compose LangFlow |
| `infra/Dockerfile.api` | Dockerfile API |
| `infra/Dockerfile.telegram` | Dockerfile Telegram |
| `api/README.md` | Документация API |
| `api/telegram/README.md` | Документация Telegram Bot |
| `api/web/README.md` | Документация Web UI |
| `langflow/README.md` | Документация LangFlow |
| `langflow/flows/Prompt Review Agent _ Human Report.json` | Flow для LangFlow |
| `n8n/langflow/Prompt Review Agent - API JSON.json` | Flow для API интеграции |

---

## FLOW ФАЙЛЫ В РЕПОЗИТОРИИ

| Файл | Назначение |
|------|------------|
| `langflow/flows/Prompt Review Agent _ Human Report.json` | Интерактивный анализ (чат) |
| `n8n/langflow/Prompt Review Agent - API JSON.json` | API-интеграция (JSON output) |

---

## ИСПРАВЛЕНИЕ ОШИБКИ

**Ошибка:** В первой версии DEPLOYMENT_GUIDE.md неверно указано "LangFlow не входит в данный репозиторий".

**Исправление:**
- Flow для анализа промптов включены в репозиторий
- Добавлена полноценная модель развёртывания LangFlow Development
- Добавлены инструкции по импорту Flow

---

## СТРУКТУРА DEPLOYMENT_GUIDE (v2.1)

| Раздел | Содержание |
|--------|------------|
| Purpose | Что разворачивается, что получит пользователь |
| Deployment Models | 4 модели: Local, Docker, LangFlow, Production |
| Prerequisites | Требования к ПО, OpenAI, Telegram |
| Environment | Все переменные с описаниями и примерами |
| Deployment | Пошаговые инструкции для каждой модели |
| Verification Checklist | Проверки API, Web UI, Telegram, LangFlow |
| Troubleshooting | Конкретные проблемы и решения |
| Recovery | Остановка, перезапуск, обновление, логи |
| Files Reference | Список ключевых файлов |

---

## МОДЕЛИ РАЗВЁРТЫВАНИЯ

| Модель | Назначение | Статус |
|--------|------------|--------|
| Local Development | Разработка и тестирование | ✅ Полностью описана |
| Docker Development | Изолированное развёртывание | ✅ Полностью описана |
| LangFlow Development | LangFlow backend с Flow из репозитория | ✅ Полностью описана |
| Production Adaptation | Основа для production | ⚠️ Требует доработки |

---

## АРХИТЕКТУРНОЕ РЕШЕНИЕ

**Принцип:** DEPLOYMENT_GUIDE должен быть полноценным Source of Truth по развёртыванию.

**Обоснование:**

1. Документ отвечает на вопрос "Как полностью развернуть проект с нуля?"
2. После прочтения инженер не должен додумывать последовательность
3. Каждый шаг имеет: команду, ожидаемый результат, проверку

---

## ИЗМЕНЁННЫЕ ФАЙЛЫ

- `docs/DEPLOYMENT_GUIDE.md` — полностью переработан (v2.0), добавлен LangFlow (v2.1)
- `README.md` — навигационный раздел со ссылкой на DEPLOYMENT_GUIDE