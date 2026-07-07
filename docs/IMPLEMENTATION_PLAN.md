# IMPLEMENTATION_PLAN.md

## Технический план реализации Prompt Review Service

**Версия:** 1.0
**Дата:** 2026-07-05
**Статус:** Утверждён

---

## Обзор плана

План описывает реализацию PEl06 — FastAPI API-слоя для Prompt Review Service. Реализация следует принципам поэтапной разработки с чёткими критериями завершения каждого этапа.

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

---

## Этап 1: Структура проекта и конфигурация

### 1.1 Цель

Создать базовую структуру проекта `api/` с конфигурационными файлами, готовыми для реализации FastAPI-сервиса.

### 1.2 Состав работ

| Задача | Описание |
|--------|----------|
| 1.1.1 | Создать каталог `api/` |
| 1.1.2 | Создать `api/requirements.txt` с зависимостями |
| 1.1.3 | Создать `api/README.md` с описанием API |
| 1.1.4 | Определить структуру подкаталогов `api/app/` |

### 1.3 Создаваемые артефакты

```
api/
├── requirements.txt
└── README.md
```

**requirements.txt:**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

**Примечание:** `.env.example` находится в `infra/` и будет актуализирован на этапе 8.

### 1.4 Зависимости

Нет зависимостей от предыдущих этапов (первый этап).

### 1.5 Критерий завершения

- [ ] Каталог `api/` создан
- [ ] `requirements.txt` содержит все необходимые зависимости
- [ ] `README.md` описывает назначение API, структуру и запуск

---

## Этап 2: Pydantic-модели и валидация

### 2.1 Цель

Определить Pydantic-модели для request/response в соответствии с JSON-контрактом из SPEC.md.

### 2.2 Состав работ

| Задача | Описание |
|--------|----------|
| 2.1.1 | Создать `api/app/schemas.py` |
| 2.1.2 | Определить `PromptReviewRequest` модель |
| 2.1.3 | Определить `PromptReviewResponse` модель |
| 2.1.4 | Определить `ErrorResponse` модель |
| 2.1.5 | Определить вспомогательные модели (Metrics, Scores, Recommendation) |
| 2.1.6 | Добавить валидацию полей (обязательные, опциональные, длины) |

### 2.3 Создаваемые артефакты

```
api/
└── app/
    ├── __init__.py
    └── schemas.py
```

**schemas.py — ключевые модели:**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NOT_APPLICABLE = "not_applicable"

class Source(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"
    N8N = "n8n"
    CLI = "cli"

class ReviewMode(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"

class Recommendation(BaseModel):
    priority: str = Field(..., pattern="^(high|medium|low)$")
    text: str

class Scores(BaseModel):
    clarity: int = Field(..., ge=0, le=10)
    specificity: int = Field(..., ge=0, le=10)
    structure: int = Field(..., ge=0, le=10)
    examples: int = Field(..., ge=0, le=10)
    constraints: int = Field(..., ge=0, le=10)
    overall: int = Field(..., ge=0, le=10)

class Metrics(BaseModel):
    characters: int
    words: int
    lines: int
    markdown_elements: Optional[int] = None

class PromptReviewRequest(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=10000)
    user_id: str = Field(..., min_length=1)
    request_id: Optional[str] = None
    source: Source = Source.WEB
    review_mode: ReviewMode = ReviewMode.STANDARD

class PromptReviewResponse(BaseModel):
    request_id: str
    user_id: str
    is_prompt: bool
    purpose: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[Recommendation] = []
    scores: Optional[Scores] = None
    quality_level: QualityLevel
    revised_prompt: Optional[str] = None
    reason: Optional[str] = None
    conversion_options: List[str] = []
    metrics: Metrics
    processing_time_ms: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict = {}
```

### 2.4 Зависимости

- Этап 1 (структура проекта)

### 2.5 Критерий завершения

- [ ] `schemas.py` создан
- [ ] Все модели из SPEC.md определены
- [ ] Валидация полей работает (Pydantic Field constraints)
- [ ] `PromptReviewRequest` валидирует обязательные поля
- [ ] `PromptReviewResponse` соответствует JSON-контракту
- [ ] Импорт моделей не вызывает ошибок

---

## Этап 3: Backend-адаптеры

### 3.1 Цель

Реализовать абстракцию для вызова Prompt Review Engine через LangFlow или LangChain с единым интерфейсом.

### 3.2 Состав работ

| Задача | Описание |
|--------|----------|
| 3.1.1 | Создать `api/app/adapters/__init__.py` |
| 3.1.2 | Создать `api/app/adapters/base.py` с абстрактным интерфейсом |
| 3.1.3 | Создать `api/app/adapters/langflow.py` для LangFlow |
| 3.1.4 | Создать `api/app/adapters/langchain.py` для LangChain |
| 3.1.5 | Реализовать фабрику адаптеров по `BACKEND_TYPE` |
| 3.1.6 | Добавить обработку ошибок и timeout |

### 3.3 Создаваемые артефакты

```
api/
└── app/
    └── adapters/
        ├── __init__.py
        ├── base.py
        ├── langflow.py
        └── langchain.py
```

**base.py — абстрактный интерфейс:**

```python
from abc import ABC, abstractmethod
from ..schemas import PromptReviewRequest, PromptReviewResponse

class BackendAdapter(ABC):
    @abstractmethod
    async def review(self, request: PromptReviewRequest) -> PromptReviewResponse:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

**langflow.py — реализация для LangFlow:**
- HTTP Request к LangFlow API (`/api/v1/run/{FLOW_ID}`)
- Аутентификация (Bearer token или x-api-key)
- Timeout handling
- Retry с exponential backoff
- Преобразование ответа LangFlow в `PromptReviewResponse`

**langchain.py — реализация для LangChain:**
- Прямой вызов LangChain pipeline
- Поддержка OpenAI API и Ollama
- Конфигурация через переменные окружения

### 3.4 Зависимости

- Этап 1 (структура проекта)
- Этап 2 (Pydantic-модели)

### 3.5 Критерий завершения

- [ ] Абстрактный интерфейс `BackendAdapter` определён
- [ ] `LangFlowAdapter` реализован с HTTP Request
- [ ] `LangChainAdapter` реализован с прямым вызовом
- [ ] Фабрика адаптеров работает по `BACKEND_TYPE`
- [ ] Обработка ошибок возвращает корректные `ErrorResponse`
- [ ] Timeout настраивается через переменные окружения

---

## Этап 4: FastAPI-сервер

### 4.1 Цель

Реализовать FastAPI-сервер с тремя эндпоинтами: `/`, `/health`, `/review`.

### 4.2 Состав работ

| Задача | Описание |
|--------|----------|
| 4.1.1 | Создать `api/app/main.py` |
| 4.1.2 | Реализовать `GET /` — корневой endpoint |
| 4.1.3 | Реализовать `GET /health` — health check |
| 4.1.4 | Реализовать `POST /review` — основной endpoint |
| 4.1.5 | Настроить CORS middleware |
| 4.1.6 | Добавить обработку исключений |
| 4.1.7 | Настроить structured logging (JSON) |
| 4.1.8 | Добавить `request_id` для корреляции логов |

### 4.3 Создаваемые артефакты

```
api/
└── app/
    ├── main.py
    ├── config.py
    └── logger.py
```

**main.py — ключевые компоненты:**

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import time

from .schemas import PromptReviewRequest, PromptReviewResponse, ErrorResponse
from .adapters import get_backend_adapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: инициализация адаптера
    app.state.adapter = get_backend_adapter()
    yield
    # Shutdown: cleanup

app = FastAPI(
    title="Prompt Review Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "up"}

@app.get("/health")
async def health():
    # Проверка backend-доступности
    return {"status": "ok"}

@app.post("/review", response_model=PromptReviewResponse)
async def review(request: PromptReviewRequest, req: Request):
    request_id = request.request_id or str(uuid.uuid4())
    start_time = time.time()
    
    try:
        response = await req.app.state.adapter.review(request)
        response.processing_time_ms = int((time.time() - start_time) * 1000)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.4 Зависимости

- Этап 1 (структура проекта)
- Этап 2 (Pydantic-модели)
- Этап 3 (Backend-адаптеры)

### 4.5 Критерий завершения

- [ ] `GET /` возвращает `{"status": "up"}`
- [ ] `GET /health` возвращает `{"status": "ok"}`
- [ ] `POST /review` валидирует request и возвращает response
- [ ] CORS настроен по `CORS_ORIGINS`
- [ ] Structured logging работает (JSON format)
- [ ] `request_id` автогенерируется и возвращается в ответе
- [ ] Ошибки возвращают корректные `ErrorResponse`

---

## Этап 5: Тестирование FastAPI

### 5.1 Цель

Выполнить ручное тестирование всех эндпоинтов FastAPI и зафиксировать результаты.

### 5.2 Состав работ

| Задача | Описание |
|--------|----------|
| 5.1.1 | Создать `api/tests.md` с тестовыми сценариями |
| 5.1.2 | Тест `GET /` — проверка доступности |
| 5.1.3 | Тест `GET /health` — health check |
| 5.1.4 | Тест `POST /review` с промптом — позитивный сценарий |
| 5.1.5 | Тест `POST /review` без промпта — негативный сценарий |
| 5.1.6 | Тест граничных случаев (пустой текст, максимальная длина, спецсимволы) |
| 5.1.7 | Проверка JSON-контракта ответа |
| 5.1.8 | Проверка обработки ошибок (400, 500, 503) |
| 5.1.9 | Тестирование через Swagger UI (`/docs`) |
| 5.1.10 | Тестирование через `curl` |
| 5.1.11 | Зафиксировать скриншоты: `/docs`, `/health`, `POST /review` |

### 5.3 Создаваемые артефакты

```
api/
└── tests.md
```

**tests.md — структура:**

```markdown
# Тестовые сценарии Prompt Review Service

## 1. Endpoint: GET /

### 1.1. Корневой endpoint
**Request:** GET /
**Expected Response:** {"status": "up"}
**Status:** ✅/❌

## 2. Endpoint: GET /health

### 2.1. Health check
**Request:** GET /health
**Expected Response:** {"status": "ok"}
**Status:** ✅/❌

## 3. Endpoint: POST /review

### 3.1. Позитивный тест: промпт хорошего качества
**Input:** ...
**Expected Output:** is_prompt=true, quality_level=good/excellent
**Status:** ✅/❌

### 3.2. Позитивный тест: промпт низкого качества
**Input:** ...
**Expected Output:** is_prompt=true, quality_level=fair/poor
**Status:** ✅/❌

### 3.3. Негативный тест: обычный текст (не промпт)
**Input:** "Привет, как дела?"
**Expected Output:** is_prompt=false, reason, conversion_options
**Status:** ✅/❌

## 4. Граничные случаи

### 4.1. Пустой текст
**Input:** prompt_text=""
**Expected Output:** 400 Bad Request, validation_error
**Status:** ✅/❌

### 4.2. Минимальная длина (10 символов)
**Input:** prompt_text="1234567890"
**Expected Output:** 200 OK или 400 (в зависимости от валидации)
**Status:** ✅/❌

### 4.3. Максимальная длина (10000 символов)
**Input:** prompt_text="..." (10000 chars)
**Expected Output:** 200 OK
**Status:** ✅/❌

## 5. Обработка ошибок

### 5.1. Отсутствует обязательное поле user_id
**Expected Output:** 400 Bad Request, validation_error
**Status:** ✅/❌

### 5.2. Некорректный JSON
**Expected Output:** 400 Bad Request
**Status:** ✅/❌
```

### 5.4 Зависимости

- Этап 4 (FastAPI-сервер)

### 5.5 Критерий завершения

- [ ] `tests.md` создан с тестовыми сценариями для всех эндпоинтов
- [ ] `GET /` возвращает `{"status": "up"}`
- [ ] `GET /health` возвращает `{"status": "ok"}`
- [ ] `POST /review` с промптом возвращает корректный JSON-ответ
- [ ] `POST /review` с обычным текстом возвращает `is_prompt=false`
- [ ] Граничные случаи обработаны (пустой текст, мин/макс длина)
- [ ] Ошибки возвращают корректные HTTP-статусы и JSON
- [ ] Тестирование через Swagger UI (`/docs`) прошло успешно
- [ ] Тестирование через `curl` прошло успешно
- [ ] Скриншоты зафиксированы: `/docs`, `/health`, `POST /review`

---

## Этап 6: Telegram Bot UI

### 6.1 Цель

Реализовать Telegram Bot, использующий FastAPI `/review` endpoint.

### 6.2 Состав работ

| Задача | Описание |
|--------|----------|
| 6.1.1 | Создать каталог `api/telegram/` |
| 6.1.2 | Реализовать Telegram Bot на `aiogram` или `python-telegram-bot` |
| 6.1.3 | Добавить обработчик сообщений |
| 6.1.4 | Формировать `user_id = "telegram:{telegram_id}"` |
| 6.1.5 | Вызывать `POST /review` через HTTP |
| 6.1.6 | Форматировать ответ для Telegram (human-readable) |
| 6.1.7 | Добавить переменные окружения: `TELEGRAM_BOT_TOKEN` |
| 6.1.8 | Создать `api/telegram/README.md` |
| 6.1.9 | **E2E-тестирование Telegram Bot** |
| 6.1.10 | Зафиксировать скриншоты: отправка промпта, ответ агента |

### 6.3 Создаваемые артефакты

```
api/
└── telegram/
    ├── bot.py
    ├── formatter.py
    ├── requirements.txt
    └── README.md
```

**bot.py — ключевые компоненты:**

```python
from aiogram import Bot, Dispatcher, types
import httpx

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    user_id = f"telegram:{message.from_user.id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.API_URL}/review",
            json={
                "user_id": user_id,
                "source": "telegram",
                "prompt_text": message.text
            }
        )
    
    result = response.json()
    formatted = format_response(result)
    await message.answer(formatted)
```

### 6.4 Зависимости

- Этап 4 (FastAPI-сервер)
- Этап 5 (Тестирование API)

### 6.5 Критерий завершения

- [ ] Telegram Bot запускается и отвечает на сообщения
- [ ] `user_id` формируется как `telegram:{id}`
- [ ] `source` устанавливается как `telegram`
- [ ] Ответ форматируется для Telegram (краткий формат)
- [ ] `is_prompt=false` обрабатывается корректно
- [ ] **E2E-тест:** Telegram Bot → FastAPI → Backend — полный цикл работает
- [ ] **E2E-тест:** Отправка промпта в Telegram — получен корректный ответ
- [ ] **E2E-тест:** Отправка обычного текста — получен ответ с conversion_options
- [ ] Скриншоты: отправка промпта, ответ агента

---

## Этап 7: Web UI

### 7.1 Цель

Реализовать простую Web-форму, использующую FastAPI `/review` endpoint.

### 7.2 Состав работ

| Задача | Описание |
|--------|----------|
| 7.1.1 | Создать каталог `api/web/` |
| 7.1.2 | Реализовать статический HTML с CSS |
| 7.1.3 | Добавить JavaScript для вызова `/review` |
| 7.1.4 | Добавить форму ввода `prompt_text` |
| 7.1.5 | Добавить генерацию `session_id` для `user_id` |
| 7.1.6 | Форматировать результат на странице |
| 7.1.7 | Добавить индикатор загрузки |
| 7.1.8 | Создать `api/web/README.md` |
| 7.1.9 | **E2E-тестирование Web UI** |
| 7.1.10 | Зафиксировать скриншоты: форма ввода, результат анализа |

### 7.3 Создаваемые артефакты

```
api/
└── web/
    ├── index.html
    ├── style.css
    ├── app.js
    └── README.md
```

**index.html — структура:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Prompt Review Service</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Prompt Review Service</h1>
    <form id="review-form">
        <textarea id="prompt-text" placeholder="Введите промпт..." required></textarea>
        <button type="submit">Проверить промпт</button>
    </form>
    <div id="result" class="hidden"></div>
    <script src="app.js"></script>
</body>
</html>
```

### 7.4 Зависимости

- Этап 4 (FastAPI-сервер)
- Этап 5 (Тестирование API)

### 7.5 Критерий завершения

- [ ] Web-форма открывается в браузере
- [ ] Форма отправляет `POST /review` с правильным JSON
- [ ] `user_id` генерируется как `session:{uuid}`
- [ ] `source` устанавливается как `web`
- [ ] Результат отображается в читаемом формате
- [ ] Индикатор загрузки работает
- [ ] **E2E-тест:** Web UI → FastAPI → Backend — полный цикл работает
- [ ] **E2E-тест:** Ввод промпта в форму — получен результат анализа
- [ ] **E2E-тест:** Ввод обычного текста — получен ответ с conversion_options
- [ ] Скриншоты: форма ввода, результат анализа

---

## Этап 8: Документация и публикация

### 8.1 Цель

Подготовить документацию и опубликовать проект на GitHub, интегрировав FastAPI-сервис в существующую инфраструктуру.

### 8.2 Контекст инфраструктуры

**Архитектурный принцип:**

> **Один сервисный контур — один docker-compose файл.**

Проект следует принципу разделения сервисных контуров:
- LangFlow разворачивается через `infra/docker-compose.langflow.yml`
- Prompt Review FastAPI разворачивается через `infra/docker-compose.api.yml`

Эти compose-файлы описывают разные сервисные контуры и не дублируют друг друга. При необходимости они взаимодействуют через существующую внешнюю сеть `n8n_default`.

**Существующие артефакты в `infra/`:**

| Файл | Назначение | Статус |
|------|------------|--------|
| `docker-compose.langflow.yml` | LangFlow + PostgreSQL | ✅ Существует |
| `.env.example` | Шаблон переменных окружения | ✅ Существует |
| `.env` | Реальные секреты (не в Git) | ✅ Существует |
| `.gitignore` | Исключения для Git | ✅ Существует |
| `README.md` | Документация инфраструктуры | ✅ Существует |

**Развёрнутые компоненты:**

| Компонент | Адрес | Статус |
|-----------|-------|--------|
| LangFlow | VPS или локальный сервер | ✅ Работает |
| PostgreSQL | Внутренний контейнер | ✅ Работает |

**Принцип реализации этапа 8:**
- Не создавать параллельную инфраструктуру
- Использовать существующие решения в `infra/`
- Добавлять новые артефакты в `infra/` при необходимости
- Актуализировать существующую документацию

### 8.3 Состав работ

| Задача | Описание |
|--------|----------|
| 8.1.1 | Актуализировать `api/README.md` |
| 8.1.2 | Добавить инструкции по запуску (локально) |
| 8.1.3 | Добавить примеры `curl` для всех эндпоинтов |
| 8.1.4 | Создать `infra/docker-compose.api.yml` для FastAPI |
| 8.1.5 | Создать `infra/Dockerfile.api` для FastAPI |
| 8.1.6 | Актуализировать `infra/.env.example` (добавить переменные FastAPI) |
| 8.1.7 | Актуализировать `infra/README.md` (добавить FastAPI) |
| 8.1.8 | Актуализировать корневой `README.md` |
| 8.1.9 | Добавить все скриншоты в `docs/screenshots/` |
| 8.1.10 | Проверить `.gitignore` в `infra/` (исключить `.env`) |

### 8.4 Создаваемые артефакты

```
api/
└── README.md (обновлён)

infra/
├── docker-compose.api.yml (новый)
├── Dockerfile.api (новый)
├── .env.example (актуализирован)
├── README.md (актуализирован)
└── .gitignore (проверен)

docs/
└── screenshots/
    ├── fastapi-docs.png
    ├── fastapi-health.png
    ├── post-review-prompt.png
    ├── post-review-not-prompt.png
    ├── telegram-input.png
    ├── telegram-output.png
    ├── web-form.png
    └── web-result.png
```

### 8.5 Docker-конфигурация FastAPI

**Принцип интеграции:**

FastAPI-сервис разворачивается аналогично LangFlow:
- Отдельный docker-compose файл для сервиса
- Использование сети `n8n_default` для публикации через Traefik
- Переменные окружения через `.env`

**docker-compose.api.yml — примерная структура:**

```yaml
services:
  prompt-review-api:
    build:
      context: ../api
      dockerfile: ../infra/Dockerfile.api
    container_name: prompt-review-api
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8000:8000"
    networks:
      - n8n_default
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  n8n_default:
    external: true
    name: n8n_default
```

**Переменные для .env.example (добавить в существующий):**

```bash
# ============================================================================
# FastAPI Configuration (PEl06)
# ============================================================================

# Backend type: langflow or langchain
BACKEND_TYPE=langflow

# LangFlow configuration (если BACKEND_TYPE=langflow)
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your_flow_id
LANGFLOW_API_KEY=your_api_key

# API configuration
API_KEY=your_api_key
CORS_ORIGINS=http://localhost:3000,https://t.me

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Limits
REQUEST_TIMEOUT_SECONDS=30
MAX_PROMPT_LENGTH=10000
```

### 8.6 Зависимости

- Этап 5 (Тестирование FastAPI)
- Этап 6 (Telegram Bot UI)
- Этап 7 (Web UI)

### 8.7 Критерий завершения

- [ ] `api/README.md` содержит:
  - Назначение API
  - Схему запроса `/review`
  - Схему ответа
  - Запуск локально (`uvicorn app.main:app`)
  - Примеры `curl`
  - Использование Telegram/Web
  - Production checklist
- [ ] `infra/docker-compose.api.yml` создан и интегрируется с существующей инфраструктурой
- [ ] `infra/Dockerfile.api` создаёт корректный образ
- [ ] `infra/.env.example` актуализирован (добавлены переменные FastAPI)
- [ ] `infra/README.md` актуализирован (добавлена секция FastAPI)
- [ ] Корневой `README.md` актуализирован
- [ ] Все скриншоты добавлены в `docs/screenshots/`
- [ ] `.gitignore` в `infra/` исключает `.env`

---

## Сводная таблица этапов

| Этап | Название | Зависимости | Ключевые артефакты |
|------|----------|--------------|-------------------|
| 1 | Структура проекта | Нет | `api/`, `requirements.txt`, `README.md` |
| 2 | Pydantic-модели | 1 | `schemas.py` |
| 3 | Backend-адаптеры | 1, 2 | `adapters/*.py` |
| 4 | FastAPI-сервер | 1, 2, 3 | `main.py`, `config.py`, `logger.py` |
| 5 | Тестирование FastAPI | 4 | `tests.md`, скриншоты API |
| 6 | Telegram Bot UI | 4, 5 | `telegram/`, E2E-тесты Telegram |
| 7 | Web UI | 4, 5 | `web/`, E2E-тесты Web |
| 8 | Документация и публикация | 5, 6, 7 | `infra/docker-compose.api.yml`, `infra/Dockerfile.api` |

**Примечание:** `.env.example` находится в `infra/` и актуализируется на этапе 8.

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| LangFlow API недоступен | Средняя | Высокое | Реализовать LangChain-адаптер как fallback |
| Timeout при долгих запросах LLM | Высокая | Среднее | Настроить timeout 30s, добавить retry |
| CORS ошибки в Web UI | Средняя | Низкое | Явный CORS allowlist, тестирование в браузере |
| Telegram Bot token leak | Низкая | Высокое | Переменные окружения, `.env` в `.gitignore` |

---

## Определение готовности (Definition of Done)

Проект PEl06 считается завершённым при выполнении:

- [ ] FastAPI предоставляет endpoint `/review`
- [ ] Prompt Review Engine доступен через HTTP API
- [ ] Единый JSON-контракт сохранён
- [ ] Telegram Bot успешно использует API
- [ ] Web-интерфейс успешно использует API
- [ ] Выполнены E2E-тесты обоих интерфейсов
- [ ] Проект документирован
- [ ] Проект опубликован на GitHub
- [ ] Архитектура естественно продолжает PEl03–PEl05
- [ ] Все этапы плана выполнены

---

## Следующие шаги после завершения

| Приоритет | Задача |
|-----------|--------|
| P1 | Production deployment (HTTPS, API key, rate limiting) |
| P2 | Мониторинг и логирование (Prometheus, Grafana) |
| P3 | CI/CD pipeline |
| P4 | Расширение функциональности (batch processing, async) |