# Prompt Review Service API

FastAPI API-слой для Prompt Review Service.

## Назначение

Публичный HTTP API для анализа качества промптов. Сервис принимает текст, определяет, является ли он промптом для LLM, и выполняет структурированный анализ с оценками, рекомендациями и улучшенной редакцией.

## Архитектура

```
Telegram / Web / n8n / CLI
          ↓
      FastAPI (/review)
          ↓
  Prompt Review Engine
          ↓
LangFlow или LangChain backend
```

**Принцип:** FastAPI не содержит бизнес-логику Prompt Review. Вся работа с Prompt Review Engine выполняется через BackendAdapter.

## Структура

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI сервер
│   ├── config.py         # Конфигурация
│   ├── logger.py         # Логирование
│   ├── schemas.py        # Pydantic модели
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py       # Абстрактный интерфейс
│   │   ├── langflow.py   # LangFlow adapter
│   │   └── langchain.py  # LangChain adapter
│   └── pipeline/
│       ├── __init__.py
│       ├── prompts.py    # Промпты для LLM
│       ├── metrics.py    # Инструментальные метрики
│       ├── classifier.py # Классификация текста
│       ├── reviewer.py   # Анализ качества
│       ├── rewriter.py   # Улучшение редакции
│       ├── composer.py   # Формирование JSON
│       └── pipeline.py   # Основной конвейер
├── requirements.txt
└── README.md
```

## Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | GET | Корневой endpoint, проверка доступности |
| `/health` | GET | Health check для мониторинга |
| `/review` | POST | Анализ промпта |

## Запуск локально

```bash
cd api
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Настройка переменных окружения
export BACKEND_TYPE=langflow
export LANGFLOW_URL=https://langflow.alex-n8n.site
export LANGFLOW_FLOW_ID=your_flow_id
export LANGFLOW_API_KEY=your_api_key

# Запуск
uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `BACKEND_TYPE` | Тип backend: `langflow` или `langchain` | Да |
| `LANGFLOW_URL` | URL LangFlow сервера | Для langflow |
| `LANGFLOW_FLOW_ID` | ID Flow в LangFlow | Для langflow |
| `LANGFLOW_API_KEY` | API ключ LangFlow | Для langflow |
| `LANGCHAIN_MODEL` | Модель для LangChain | Для langchain |
| `API_KEY` | API ключ для аутентификации | Нет |
| `CORS_ORIGINS` | Разрешённые origins (через запятую) | Нет |
| `LOG_LEVEL` | Уровень логирования | Нет (default: INFO) |
| `REQUEST_TIMEOUT_SECONDS` | Timeout запросов к backend | Нет (default: 30) |
| `MAX_PROMPT_LENGTH` | Максимальная длина промпта | Нет (default: 10000) |

## Примеры запросов

### POST /review

**Запрос:**
```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "prompt_text": "Ты — опытный преподаватель Python. Объясни, что такое словарь."
  }'
```

**Ответ (промпт):**
```json
{
  "request_id": "req_...",
  "user_id": "user_123",
  "is_prompt": true,
  "purpose": "Обучение работе со словарями Python",
  "strengths": ["Чёткая ролевая инструкция", "Конкретная задача"],
  "weaknesses": ["Отсутствуют ограничения по объёму"],
  "recommendations": [{"priority": "medium", "text": "Указать ожидаемый объём ответа"}],
  "scores": {
    "clarity": 8,
    "specificity": 7,
    "structure": 9,
    "examples": 4,
    "constraints": 5,
    "overall": 7
  },
  "quality_level": "good",
  "revised_prompt": "...",
  "metrics": {...},
  "processing_time_ms": 1234
}
```

**Ответ (не промпт):**
```json
{
  "request_id": "req_...",
  "user_id": "user_123",
  "is_prompt": false,
  "reason": "Текст представляет собой обычное приветствие",
  "conversion_options": [
    "Добавьте ролевую инструкцию",
    "Укажите ожидаемый формат результата"
  ],
  "quality_level": "not_applicable",
  "metrics": {...}
}
```

## Swagger UI

После запуска доступна интерактивная документация:
- http://localhost:8000/docs — Swagger UI
- http://localhost:8000/redoc — ReDoc

## Backend-адаптеры

### LangFlow Adapter

Вызывает LangFlow через HTTP API:

```
FastAPI → HTTP Request → LangFlow API → LLM → JSON Response
```

### LangChain Adapter

Выполняет LangChain pipeline напрямую через PromptReviewPipeline:

```
FastAPI → LangChainAdapter → PromptReviewPipeline → LLM → JSON Response
```

**Конвейер:**

1. `collect_metrics` — инструментальный расчёт метрик промпта
2. `classify_prompt` — классификация текста через LLM (является ли промптом)
3. `review_prompt` — анализ качества через LLM (оценки, рекомендации)
4. `rewrite_prompt` — улучшенная редакция через LLM
5. `compose_result` — формирование JSON-ответа

**Переключение между адаптерами:** переменная `BACKEND_TYPE`.

**Модели LangChain:**

| Модель | Переменная | Описание |
|--------|-----------|----------|
| OpenAI | `LANGCHAIN_MODEL=openai` | Требует `OPENAI_API_KEY` |
| Ollama | `LANGCHAIN_MODEL=ollama` | Локальные модели, требует `OLLAMA_BASE_URL` |

**Архитектурное примечание:**

`PromptReviewPipeline` архитектурно выделен как внутренний модуль. В будущем возможен вынос в отдельный LangChain Service API с сохранением интерфейса адаптера.

## Переменные окружения для LangChain

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `LANGCHAIN_MODEL` | Модель: `openai` или `ollama` | Для langchain |
| `OPENAI_API_KEY` | API ключ OpenAI | Для openai |
| `OLLAMA_BASE_URL` | URL Ollama сервера | Для ollama (default: http://localhost:11434) |
| `OLLAMA_MODEL` | Модель Ollama | Для ollama (default: gemma2:9b) |