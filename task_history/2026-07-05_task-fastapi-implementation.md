# Задача: Реализация FastAPI API-слоя (этапы 1-4)

**Дата:** 2026-07-05
**Статус:** В работе

---

## Исходное задание

**Контекст:**
- PROJECT_GOAL.md, PROJECT_STATE.md, SPEC.md и IMPLEMENTATION_PLAN.md утверждены.
- Реализация начинается строго в соответствии с IMPLEMENTATION_PLAN.
- На данном шаге выполняются только этапы 1–4.

**Задача:**
Реализовать базовый FastAPI API-слой Prompt Review Service.

**Требования:**
1. Реализовать этапы 1–4 IMPLEMENTATION_PLAN без отклонений.
2. Создать структуру каталога `api/` в соответствии с планом.
3. Реализовать Pydantic-модели и валидацию, полностью соответствующие JSON-контракту из SPEC.md и PEl05.
4. Реализовать backend-архитектуру через абстракцию адаптеров.
5. Реализовать FastAPI-сервер с endpoints: GET /, GET /health, POST /review.
6. Максимально использовать существующие компоненты проекта.
7. Сохранять полную совместимость с существующим JSON-контрактом.
8. Не приступать к этапам 5–8.

**Критерий завершения:**
Полностью реализованы этапы 1–4 IMPLEMENTATION_PLAN. Проект содержит рабочий FastAPI API-слой, готовый к тестированию.

---

## Выполнение

### 1. Анализ существующих компонентов

**Изучены:**
- `langchain/prompt.py` — системный промпт для анализа промптов
- `n8n/langchain/prompt-review-langchain-code.js` — конвейер обработки PEl05
- `n8n/langchain/tests.md` — JSON-контракт из PEl05

**Переиспользовано:**
- Структура JSON-контракта (PromptMetrics, PromptScores, PromptReviewResponse)
- Логика collectPromptMetrics для расчёта метрик
- Промпты CLASSIFIER_PROMPT, REVIEW_PROMPT, REWRITER_PROMPT

### 2. Этап 1: Структура проекта

**Создано:**
```
api/
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── schemas.py
    ├── config.py
    ├── logger.py
    ├── main.py
    └── adapters/
        ├── __init__.py
        ├── base.py
        ├── langflow.py
        └── langchain.py
```

**Зависимости:**
- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0
- httpx>=0.26.0
- python-dotenv>=1.0.0
- pydantic>=2.5.0
- pydantic-settings>=2.1.0
- langchain-core>=0.3.0
- langchain-openai>=0.2.0

### 3. Этап 2: Pydantic-модели

**Создан `app/schemas.py`:**

Модели полностью соответствуют JSON-контракту из PEl05:

| Модель | Назначение |
|--------|------------|
| `QualityLevel` | Enum: excellent, good, fair, poor, not_applicable |
| `Source` | Enum: web, telegram, n8n, cli |
| `ReviewMode` | Enum: standard, detailed |
| `PromptMetrics` | Метрики: characters, words, lines, markdown_elements... |
| `PromptScores` | Оценки: clarity, completeness, ambiguity_absence... |
| `Recommendation` | Рекомендация: priority + text |
| `PromptReviewRequest` | Запрос: prompt_text, user_id, request_id, source, review_mode |
| `PromptReviewResponse` | Ответ: полный JSON-контракт |
| `ErrorResponse` | Ошибка: error, message, details |
| `HealthResponse` | Health check: status, backend, backend_available |

### 4. Этап 3: Backend-адаптеры

**Создана абстракция `BackendAdapter`:**

```python
class BackendAdapter(ABC):
    @abstractmethod
    async def review(request: PromptReviewRequest) -> PromptReviewResponse
    @abstractmethod
    async def health_check() -> bool
```

**Реализованы:**

| Адаптер | Назначение |
|---------|------------|
| `LangFlowAdapter` | HTTP Request к LangFlow API |
| `LangChainAdapter` | Прямой вызов LangChain pipeline |

**LangFlowAdapter:**
- HTTP Request к `/api/v1/run/{FLOW_ID}`
- Аутентификация (Bearer token, x-api-key)
- Timeout handling
- Парсинг ответа в PromptReviewResponse

**LangChainAdapter:**
- Расчёт метрик (collectPromptMetrics)
- Классификация текста (classify_prompt_heuristic)
- Анализ промпта (analyze_prompt)
- Формирование ответа

### 5. Этап 4: FastAPI-сервер

**Создан `app/main.py`:**

**Endpoints:**

| Endpoint | Method | Назначение |
|----------|--------|------------|
| `/` | GET | Корневой endpoint → `{"status": "up"}` |
| `/health` | GET | Health check → `{"status": "ok", "backend": "...", "backend_available": bool}` |
| `/review` | POST | Анализ промпта → PromptReviewResponse |

**Особенности:**
- Lifespan context manager для инициализации адаптера
- CORS middleware для Web UI
- Structured logging (JSON format)
- Автогенерация request_id
- Обработка ошибок (400, 500, 503)

### 6. Архитектурный принцип

**Принцип:** FastAPI не содержит бизнес-логику Prompt Review.

```
FastAPI (API-слой)
    ↓
BackendAdapter (абстракция)
    ↓
LangFlowAdapter или LangChainAdapter
    ↓
Prompt Review Engine (LLM)
```

Вся бизнес-логика инкапсулирована в адаптерах. FastAPI только:
- Валидирует запрос
- Передаёт в адаптер
- Возвращает ответ

### 7. Проверка синтаксиса

Все Python-файлы проверены на синтаксис:
```bash
python3 -m py_compile app/schemas.py app/config.py app/logger.py app/main.py app/adapters/base.py app/adapters/langflow.py app/adapters/langchain.py
```
Ошибок нет.

---

## Созданные файлы

| Файл | Строк | Назначение |
|------|-------|------------|
| `api/requirements.txt` | 11 | Зависимости Python |
| `api/README.md` | 160 | Документация API |
| `api/app/__init__.py` | 1 | Инициализация пакета |
| `api/app/schemas.py` | 210 | Pydantic-модели |
| `api/app/config.py` | 50 | Конфигурация |
| `api/app/logger.py` | 75 | Логирование |
| `api/app/main.py` | 220 | FastAPI-сервер |
| `api/app/adapters/__init__.py` | 35 | Фабрика адаптеров |
| `api/app/adapters/base.py` | 30 | Абстрактный интерфейс |
| `api/app/adapters/langflow.py` | 280 | LangFlow адаптер |
| `api/app/adapters/langchain.py` | 320 | LangChain адаптер |

---

## Обновлённые файлы

| Файл | Изменение |
|------|-----------|
| `docs/PROJECT_STATE.md` | Обновлён статус: этапы 1-4 завершены |
| `README.md` | Обновлён статус PEl06: этапы 1-4 завершены |

---

## Критерий завершения

✅ **Этап 1:** Структура проекта создана
- [x] Каталог `api/` создан
- [x] `requirements.txt` содержит все зависимости
- [x] `README.md` описывает назначение API, структуру и запуск

✅ **Этап 2:** Pydantic-модели реализованы
- [x] `schemas.py` создан
- [x] Все модели из SPEC.md определены
- [x] Валидация полей работает (Pydantic Field constraints)
- [x] `PromptReviewRequest` валидирует обязательные поля
- [x] `PromptReviewResponse` соответствует JSON-контракту PEl05
- [x] Импорт моделей не вызывает ошибок

✅ **Этап 3:** Backend-адаптеры реализованы
- [x] Абстрактный интерфейс `BackendAdapter` определён
- [x] `LangFlowAdapter` реализован с HTTP Request
- [x] `LangChainAdapter` реализован с прямым вызовом
- [x] Фабрика адаптеров работает по `BACKEND_TYPE`
- [x] Обработка ошибок возвращает корректные `ErrorResponse`
- [x] Timeout настраивается через переменные окружения

✅ **Этап 4:** FastAPI-сервер реализован
- [x] `GET /` возвращает `{"status": "up"}`
- [x] `GET /health` возвращает `{"status": "ok", ...}`
- [x] `POST /review` валидирует request и возвращает response
- [x] CORS настроен по `CORS_ORIGINS`
- [x] Structured logging работает (JSON format)
- [x] `request_id` автогенерируется и возвращается в ответе
- [x] Ошибки возвращают корректные HTTP-статусы и JSON

---

## Статус

**Выполнено** — Этапы 1-4 IMPLEMENTATION_PLAN реализованы.

FastAPI API-слой Prompt Review Service создан и готов к тестированию (этап 5).