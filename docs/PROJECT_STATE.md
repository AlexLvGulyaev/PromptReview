# PROJECT_STATE.md

## Project Summary

**Prompt Review Service** — AI-сервис для анализа качества пользовательских промптов, прошедший путь от учебного прототипа (PEl03) до готовности к production-упаковке (PEl06).

Сервис анализирует промпты, выявляет сильные и слабые стороны, оценивает качество по инженерным критериям, предлагает рекомендации по улучшению и генерирует улучшенную редакцию промпта. Важно: агент рассматривает входной текст как объект инженерного анализа, а не как задачу для выполнения.

---

## Current Status

**PEl06 — FastAPI API-слой. Проект опубликован и включён в AI Portfolio.**

Все этапы (1-8) завершены. Проект опубликован на GitHub (первая публичная версия — 2026-07-06) и включён в витрину AI Portfolio как полноценный finished-case (2026-08-27).

**Решение по backend-движкам (2026-08-28):**
- **LangChain** — основной сценарий: полный контроль над пайплайном в коде, поддержка OpenAI и Ollama (`BACKEND_TYPE=langchain`)
- **LangFlow** — фоллбэк-сценарий: визуальный flow, логика анализа редактируется без изменения кода
- Выбор движка — переменная окружения `BACKEND_TYPE`, без изменения кода

**Завершённые этапы:**
- ✅ **Этап 1:** Структура проекта `api/` с requirements.txt и README.md
- ✅ **Этап 2:** Pydantic-модели, соответствующие JSON-контракту PEl05
- ✅ **Этап 3:** Backend-адаптеры (LangFlowAdapter, LangChainAdapter)
- ✅ **Этап 4:** FastAPI-сервер с endpoints GET /, GET /health, POST /review
- ✅ **Этап 5:** Тестирование FastAPI (tests.md, скриншоты)
- ✅ **Этап 6:** Telegram Bot UI (bot.py, formatter.py, README.md)
- ✅ **Этап 7:** Web UI (index.html, styles.css, app.js, README.md)
- ✅ **Этап 8:** Production-упаковка (Docker, CORS, логирование, документация)

**Публичные интерфейсы:**
- **Web UI** — доступен после локального развёртывания (см. DEPLOYMENT_GUIDE.md)
- **REST API** — доступен после запуска сервиса
- **Telegram Bot** — может быть подключён при наличии собственного bot token (см. DEPLOYMENT_GUIDE.md)

---

## Market Validation

**Учебный контекст:** Проект развивается в рамках Module 7 (LangChain & Agents) учебного курса, охватывающего:

| Урок | Фокус | Технологии |
|------|-------|------------|
| PEl03 | MVP в LangFlow | LangFlow, шаблоны, визуальный конструктор |
| PEl04 | Агенты в LangChain | LangChain, AgentExecutor, Tools, Ollama |
| PEl05 | Интеграции с n8n | n8n + LangFlow, n8n + LangChain |
| PEl06 | Production API | FastAPI, Telegram UI, Web UI |

**Потенциал коммерциализации:**
- Автоматизация ревью промптов в AI-разработке
- Интеграция в CI/CD пайплайны для проверки качества промптов
- Встраивание в CRM-системы для анализа инструкций клиентам

---

## Commercial Assessment

| Критерий | Оценка | Обоснование |
|----------|--------|-------------|
| **Спрос** | ✅ Высокий | AI-разработчики нуждаются в инструментах качества промптов |
| **Комплексность** | ✅ Подходит | 4 архитектурных варианта (LangFlow, LangChain Chain, n8n+LangFlow, n8n+LangChain) |
| **Сроки** | ✅ До 10 дней | Техническая база готова, нужен только API-слой |
| **Риски** | ⚠️ Средние | Зависимость от внешних LLM API, требуется production-безопасность |

---

## Key Technology Areas

### Реализованные компоненты

| Компонент | Технология | Статус | Каталог |
|-----------|------------|--------|---------|
| **LangFlow MVP** | LangFlow + OpenAI API | ✅ Завершён | `langflow/` |
| **LangChain Chain** | LangChain + Ollama | ✅ Завершён | `langchain/` |
| **n8n + LangFlow** | n8n workflow | ✅ Завершён | `n8n/` |
| **n8n + LangChain** | n8n LangChain Code node | ✅ Завершён | `n8n/` |
| **Инфраструктура** | Docker, PostgreSQL, VPS | ✅ Развёрнута | `infra/` |
| **FastAPI API** | Python, FastAPI, Pydantic | ✅ Завершён | `api/` |
| **PromptReviewPipeline** | LangChain, LLM | ✅ Реализован | `api/app/pipeline/` |
| **Telegram Bot** | aiogram 3.x, HTML formatting | ✅ Завершён | `api/telegram/` |
| **Web UI** | HTML5, CSS3, Vanilla JS | ✅ Завершён | `api/web/` |

### Архитектурная эволюция

```
PEl03: LangFlow MVP (локальный прототип)
   ↓
PEl04: LangChain Chain/AgentExecutor (контролируемый код)
   ↓
PEl05: n8n + AI-backend (два интеграционных сценария)
   ↓
PEl06: FastAPI API-слой (production-ready сервис)
```

### Backend-варианты

**Сценарий 1: LangFlow**
- Размещение: VPS или локальный сервер
- Runtime: OpenAI API
- Интеграция: HTTP Request из n8n/FastAPI

**Сценарий 2: LangChain Code**
- Размещение: Внутри n8n workflow или отдельный сервис
- Runtime: OpenAI API (через ai_languageModel)
- Интеграция: Прямой вызов из n8n Code node

### JSON-контракт (единый для всех сценариев)

```json
{
  "request_id": "req_001",
  "user_id": "user_123",
  "is_prompt": true,
  "purpose": "...",
  "strengths": [],
  "weaknesses": [],
  "recommendations": [],
  "scores": {},
  "quality_level": "good",
  "revised_prompt": "...",
  "reason": null,
  "conversion_options": [],
  "metrics": {},
  "processing_time_ms": 1234
}
```

### Технологические компетенции

| Область | Компетенция | Дефицит |
|---------|-------------|---------|
| LangFlow | ✅ Полная | Нет |
| LangChain | ✅ Полная | Нет |
| n8n интеграции | ✅ Полная | Нет |
| FastAPI | ✅ Завершён | Нет |
| PromptReviewPipeline | ✅ Реализован | Нет |
| Telegram Bot | ✅ Завершён | Нет |
| Web UI | ✅ Завершён | Нет |

---

## Decision

**Принято:** Реализовать FastAPI API-слой (PEl06) с сохранением архитектурной преемственности PEl03–PEl05.

**Архитектура:**

```
Telegram / Web / n8n / CLI
          ↓
      FastAPI (/review)
          ↓
  Prompt Review Engine
          ↓
LangFlow или LangChain backend
```

**Ключевые принципы:**
1. FastAPI — публичный API-слой, не калькулятор (endpoint `/review`, не `/multiply`)
2. Единый JSON-контракт сохраняется от PEl05
3. Backend-вариантность: LangFlow или LangChain по конфигурации
4. Два UI-сценария: Telegram Bot и Web Form

---

## Next Steps

| Приоритет | Задача | Артефакт |
|-----------|--------|----------|
| ~~P1~~ | ~~Тестирование FastAPI~~ | ~~`api/tests.md`, скриншоты~~ ✅ |
| ~~P2~~ | ~~Реализовать Telegram UI~~ | ~~Telegram Bot → `/review`~~ ✅ |
| ~~P2~~ | ~~Реализовать Web UI~~ | ~~Web UI → `/review`~~ ✅ |
| ~~P3~~ | ~~Production checklist~~ | ~~HTTPS, CORS, logging~~ ✅ |
| ~~P4~~ | ~~Публикация на GitHub~~ | ~~Репозиторий~~ ✅ (2026-07-06) |
| P1 | Deployment Validation — воспроизведение развёртывания с нуля по DEPLOYMENT_GUIDE.md в чистом окружении | Deployment Validation Report |
| P2 | Оптимизация промптов (A/B-тестирование) | Отдельная задача |
| P3 | Инженерные улучшения пайплайна: учёт токенов, retry-логика в LangChainAdapter, production-логи/метрики | Требует решения владельца |
| P5 | Рассмотреть вынос PromptReviewPipeline в отдельный сервис | Архитектурная опция |

---

## Status History

| Дата | Статус | Изменение |
|------|--------|-----------|
| 2026-07-03 | PEl03 завершён | LangFlow MVP |
| 2026-07-03 | PEl04 завершён | LangChain Chain + AgentExecutor |
| 2026-07-04 | PEl05.1 завершён | n8n + LangFlow интеграция |
| 2026-07-04 | PEl05.2 завершён | n8n + LangChain Code node |
| 2026-07-05 | PEl06 определён | Discovery завершён, PROJECT_GOAL.md создан |
| 2026-07-05 | SOT актуализирован | PROJECT_STATE.md, SPEC.md, IMPLEMENTATION_PLAN.md созданы |
| 2026-07-05 | PEl06 этапы 1-4 | FastAPI API-слой реализован |
| 2026-07-05 | LangChainAdapter доработан | PromptReviewPipeline реализован, полноценный LLM-backend |
| 2026-07-05 | Этап 5 завершён | FastAPI API протестирован, tests.md создан, скриншоты сохранены |
| 2026-07-05 | Этап 6 завершён | Telegram Bot UI реализован, протестирован в Telegram |
| 2026-07-05 | Этап 7 завершён | Web UI реализован на основе дизайн-системы Lead Qualification |
| 2026-07-06 | PEl06 завершён | Production-упаковка: Docker, CORS, логирование, документация |
| 2026-07-06 | Публикация на GitHub | Первая публичная версия Prompt Review Service |
| 2026-07-07 | Финализация документации | Полировка README, удаление внутренних артефактов из публичного репозитория |
| 2026-07-08 | Исправление маппинга quality_level | Ключ `"poor"` больше не дефолтит в `GOOD`; синхронизация порогов эвристики |
| 2026-08-28 | Ротация `LANGFLOW_SECRET_KEY` | Секрет перевыпущен и обновлён в окружении; упоминания в технической документации замаскированы |
| 2026-08-28 | Решение по backend-движкам | LangChain — основной сценарий, LangFlow — фоллбэк; выбор через `BACKEND_TYPE` |
| 2026-08-28 | Включение в AI Portfolio | Проект допущен в базу знаний витрины AI Portfolio; статус — полноценный finished-case |
| 2026-08-30 | Актуализация Project State | PROJECT_STATE.md приведён в соответствие с фактическим состоянием; зафиксирован остаточный долг (Deployment Validation, оптимизация промптов, инженерные улучшения) |