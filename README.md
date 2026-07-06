# Prompt Review Service

AI-сервис для анализа качества пользовательских промптов. Проходит путь от учебного прототипа до production-ready API.

---

## Описание

**Prompt Review Service** анализирует промпты, выявляет сильные и слабые стороны, оценивает качество по инженерным критериям, предлагает рекомендации по улучшению и генерирует улучшенную редакцию.

Ключевая характеристика: агент рассматривает входной текст как **объект инженерного анализа**, а не как задачу для выполнения. Он не выполняет промпт, не принимает указанную роль, сохраняет исходную цель и аудиторию.

---

## Архитектурная эволюция

Проект демонстрирует эволюцию AI-решения от прототипа до production-сервиса:

| Этап | Технология | Ключевое достижение | Статус |
|------|------------|---------------------|--------|
| **PEl03** | LangFlow | MVP Prompt Review Agent | ✅ Завершён |
| **PEl04** | LangChain | Chain + AgentExecutor + Tool | ✅ Завершён |
| **PEl05** | n8n | Две интеграционные архитектуры | ✅ Завершён |
| **PEl06** | FastAPI | Публичный API-слой /review | ✅ Завершён |

### Итоговая архитектура

```
Telegram / Web / n8n / CLI
          ↓
      FastAPI (/review)
          ↓
  Prompt Review Engine
          ↓
LangFlow или LangChain backend
```

---

## Реализации

### PEl03: LangFlow MVP

**Каталог:** `langflow/`

**Назначение:** Прототип Prompt Review Agent на базе визуального конструктора LangFlow.

**Ключевые особенности:**
- Основан на шаблоне Basic Prompting
- Минимальные изменения — только системный промпт
- Классификация: промпт или обычный текст
- Структурированный анализ качества

**Артефакты:**
- `langflow/README.md` — документация
- Flow JSON для импорта

---

### PEl04: LangChain Chain / AgentExecutor

**Каталог:** `langchain/`

**Назначение:** Локальная реализация на LangChain с поддержкой двух режимов работы.

**Ключевые особенности:**
- **Chain mode** — линейный поток без инструментов
- **AgentExecutor mode** — режим с Tool Calling
- Инструмент `prompt_metrics` для расчёта метрик
- Поддержка локальных моделей через Ollama

**Артефакты:**
- `langchain/main.py` — Chain-реализация
- `langchain/main_agent.py` — AgentExecutor-реализация
- `langchain/tools/prompt_metrics.py` — инструмент метрик

**Модели:**
- `llama3.2:1b` — быстрый анализ простых промптов
- `gemma4:e4b` — глубокий анализ сложных промптов

---

### PEl05: n8n интеграции

**Каталог:** `n8n/`

**Назначение:** Интеграция AI-компонентов с оркестратором n8n.

#### Сценарий 1: n8n + LangFlow ✅

**Архитектура:**
```
n8n Workflow → HTTP Request → LangFlow API → Structured Output → JSON
```

**Ключевые особенности:**
- LangFlow развёрнут на VPS (Docker + PostgreSQL)
- OpenAI API для инференса
- Единый JSON-контракт

#### Сценарий 2: n8n + LangChain ✅

**Архитектура:**
```
Chat Trigger → LangChain Code → OpenAI Chat Model → JSON Output
```

**Ключевые особенности:**
- Вся интеллектуальная логика внутри n8n
- Конвейер обработки с ветвлением
- Классификатор текста (промпт/не промпт)
- Автономный workflow без внешних зависимостей

**Конвейер обработки:**
```
extractInput → collectPromptMetrics → classifyPrompt
                    ↓
         is_prompt=false → composeNotPrompt → JSON
         is_prompt=true  → reviewPrompt → rewritePrompt → composeResult → JSON
```

**Артефакты:**
- `n8n/README.md` — документация сценариев
- `n8n/langchain/README.md` — детали сценария 2
- `n8n/langchain/tests.md` — тестовые примеры

---

### PEl06: FastAPI API-слой

**Каталог:** `api/`

**Назначение:** Production-ready API-сервис с endpoint `/review`.

**Публичные точки входа:**
- **Web UI:** https://prompt-review-demo.alex-n8n.site
- **API:** https://prompt-review-api.alex-n8n.site
- **Swagger UI:** https://prompt-review-api.alex-n8n.site/docs
- **ReDoc:** https://prompt-review-api.alex-n8n.site/redoc
- **Telegram Bot:** @OptimusPromptReview_bot

**Ключевые особенности:**
- Публичный HTTP API с HTTPS
- Единый JSON-контракт от PEl05
- Backend-вариантность: LangFlow или LangChain
- Два UI-сценария: Telegram Bot и Web UI

**Реализованные этапы:**
- ✅ Структура проекта `api/`
- ✅ Pydantic-модели (`schemas.py`)
- ✅ Backend-адаптеры (`LangFlowAdapter`, `LangChainAdapter`)
- ✅ FastAPI-сервер (endpoints: `/`, `/health`, `/review`)
- ✅ Тестирование FastAPI (`tests.md`)
- ✅ Telegram Bot UI (aiogram 3.x, HTML formatting)
- ✅ Web UI (HTML5, CSS3, Vanilla JS)
- ✅ Production-упаковка (Docker, CORS, логирование)

**Telegram Bot UI:**
- Каталог `api/telegram/`
- aiogram 3.x с HTML-форматированием
- Обработка ошибок API
- Документация (`api/telegram/README.md`)

**Web UI:**
- Каталог `api/web/`
- Тёмная тема на основе Lead Qualification дизайн-системы
- Адаптивная вёрстка (desktop, tablet, mobile)
- Прогресс-бары для визуализации оценок
- Карточки с цветными акцентами
- Документация (`api/web/README.md`)

**Безопасность:**
- CORS только для доверенных origin
- HTTPS через Traefik
- Секреты в `.env` (не коммитятся в Git)
- Структурированное JSON-логирование

**Спецификация:** `docs/SPEC.md`
**План реализации:** `docs/IMPLEMENTATION_PLAN.md`

---

## Инфраструктура

**Каталог:** `infra/`

**Развёрнутые компоненты:**

| Компонент | Адрес | Статус |
|-----------|-------|--------|
| **LangFlow** | https://langflow.alex-n8n.site | ✅ Running |
| **PostgreSQL** | Внутренний контейнер | ✅ Running |
| **FastAPI API** | https://prompt-review-api.alex-n8n.site | ✅ Running |
| **Web UI** | https://prompt-review-demo.alex-n8n.site | ✅ Running |

**Docker-контейнеры:**
- `prompt-review-langflow` — LangFlow 1.10.1
- `prompt-review-postgres` — PostgreSQL 16
- `prompt-review-api` — FastAPI Service

**Документация:**
- `infra/README.md` — статус инфраструктуры и инструкции по развёртыванию
- `infra/docker-compose.langflow.yml` — LangFlow + PostgreSQL
- `infra/docker-compose.api.yml` — FastAPI Service
- `infra/Dockerfile.api` — Dockerfile для FastAPI

---

## Документация

| Документ | Назначение |
|----------|------------|
| `docs/PROJECT_STATE.md` | Паспорт состояния проекта |
| `docs/SPEC.md` | Продуктовая спецификация PEl06 |
| `docs/IMPLEMENTATION_PLAN.md` | Технический план реализации (будет создан) |
| `docs/deployment/` | Деплоймент-документация |
| `docs/screenshots/` | Скриншоты для отчётов |

---

## История задач

**Каталог:** `task-history/`

Каждая задача фиксируется в отдельном файле с исходным заданием и результатами выполнения.

---

## Входные материалы

**Каталог:** `attachments/input/`

Учебные материалы Module 7 (LangChain & Agents):
- `PEl03.md` — LangFlow MVP
- `PEl04.md` — LangChain Agents
- `PEl05.md` — n8n интеграции
- `PEl06.md` — FastAPI API-слой

**Каталог:** `attachments/reports/`

PDF-отчёты по завершённым урокам.

---

## JSON-контракт

Единый формат ответа для всех реализаций:

```json
{
  "request_id": "req_001",
  "user_id": "user_123",
  "is_prompt": true,
  "purpose": "Назначение промпта",
  "strengths": ["Сильная сторона 1", "Сильная сторона 2"],
  "weaknesses": ["Слабая сторона 1"],
  "recommendations": [
    {"priority": "high", "text": "Рекомендация 1"},
    {"priority": "medium", "text": "Рекомендация 2"}
  ],
  "scores": {
    "clarity": 8,
    "specificity": 7,
    "structure": 9,
    "examples": 4,
    "constraints": 5,
    "overall": 7
  },
  "quality_level": "good",
  "revised_prompt": "Улучшенная редакция...",
  "reason": null,
  "conversion_options": [],
  "metrics": {
    "characters": 450,
    "words": 67,
    "lines": 12
  },
  "processing_time_ms": 2345
}
```

---

## Следующие шаги

| Приоритет | Задача | Статус |
|-----------|--------|--------|
| ~~P1~~ | ~~Реализовать FastAPI endpoint `/review`~~ | ✅ Готово |
| ~~P1~~ | ~~Создать структуру `api/`~~ | ✅ Готово |
| ~~P2~~ | ~~Реализовать Telegram Bot UI~~ | ✅ Готово |
| ~~P2~~ | ~~Реализовать Web UI~~ | ✅ Готово |
| ~~P3~~ | ~~Production-упаковка~~ | ✅ Готово |
| P4 | Публикация на GitHub | 📋 Планируется |

---

## Быстрый старт

### Локальный запуск

```bash
# Клонировать репозиторий
git clone <repo-url>
cd prompt-review

# Установить зависимости
cd api
pip install -r requirements.txt

# Создать .env из шаблона
cp ../infra/.env.example ../infra/.env
# Отредактировать ../infra/.env с вашими ключами

# Запустить FastAPI
uvicorn app.main:app --reload --port 8000
```

### Проверка

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs

# Пример запроса
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Напиши функцию сортировки списка на Python", "user_id": "test_user"}'
```

### Docker-развёртывание

```bash
cd infra

# Запуск LangFlow + PostgreSQL
docker compose -f docker-compose.langflow.yml up -d

# Запуск FastAPI API
docker compose -f docker-compose.api.yml up -d --build
```

---

## Контакты

Проект развивается в рамках AI Automation Portfolio Lab.