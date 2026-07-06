# SPEC.md — Prompt Review Service

## Продуктовая спецификация

**Версия:** 1.0
**Дата:** 2026-07-05
**Статус:** Утверждена

---

## 1. Обзор продукта

### 1.1 Назначение

Prompt Review Service — AI-сервис для анализа качества пользовательских промптов. Сервис принимает текст, определяет, является ли он промптом для LLM, и выполняет структурированный анализ с оценками, рекомендациями и улучшенной редакцией.

### 1.2 Ключевая характеристика

Агент рассматривает входной текст как **объект инженерного анализа**, а не как задачу для выполнения. Он:
- Не выполняет анализируемый промпт
- Не принимает роль, указанную внутри промпта
- Не изменяет исходную задачу пользователя
- Сохраняет исходную цель, аудиторию и бизнес-смысл

### 1.3 Целевая аудитория

| Сегмент | Потребность |
|---------|-------------|
| AI-разработчики | Проверка качества промптов перед использованием |
| Команды разработки | Интеграция в CI/CD для валидации промптов |
| Бизнес-пользователи | Анализ инструкций для AI-ассистентов |

---

## 2. Архитектура

### 2.1 Общая схема

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                        │
│         Telegram Bot │ Web Form │ n8n │ CLI               │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP POST
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Layer                          │
│                                                           │
│  GET  /           → {"status": "up"}                      │
│  GET  /health     → {"status": "ok"}                     │
│  POST /review     → PromptReviewResponse                  │
│                                                           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                Prompt Review Engine                       │
│                                                           │
│  1. extractInput        → извлечение текста              │
│  2. collectPromptMetrics → расчёт метрик                  │
│  3. classifyPrompt      → определение типа текста        │
│  4. [if prompt]                                            │
│       reviewPrompt      → анализ качества                 │
│       rewritePrompt     → улучшенная редакция             │
│     [else]                                                 │
│       composeNotPrompt  → альтернативы                    │
│  5. composeResult       → формирование JSON-ответа       │
│                                                           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend Adapters                         │
│                                                           │
│  LangFlow Adapter  │  LangChain Adapter                  │
│  (HTTP to LangFlow) │ (Direct execution)                  │
│                                                           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   LLM Runtime                             │
│                                                           │
│  OpenAI API  │  Ollama (local)                           │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Backend-варианты

| Вариант | Реализация | Конфигурация |
|---------|-------------|--------------|
| **LangFlow** | HTTP Request к LangFlow API | `LANGFLOW_URL`, `LANGFLOW_FLOW_ID`, `LANGFLOW_API_KEY` |
| **LangChain** | Прямой вызов LangChain | `LANGCHAIN_MODE=local`, модель в конфигурации |

### 2.3 Эволюция архитектуры

| Этап | Технология | Ключевое достижение |
|------|------------|---------------------|
| **PEl03** | LangFlow | MVP Prompt Review Agent |
| **PEl04** | LangChain | Chain + AgentExecutor + Tool |
| **PEl05** | n8n | Две интеграционные архитектуры |
| **PEl06** | FastAPI | Публичный API-слой /review |

---

## 3. API Specification

### 3.1 Endpoint: GET /

Корневой endpoint для проверки доступности сервиса.

**Request:**
```http
GET /
```

**Response:**
```json
{
  "status": "up"
}
```

### 3.2 Endpoint: GET /health

Health check для мониторинга и оркестрации.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### 3.3 Endpoint: POST /review

Основной endpoint для анализа промптов.

**Request:**
```http
POST /review
Content-Type: application/json

{
  "request_id": "req_001",
  "user_id": "user_123",
  "source": "web",
  "review_mode": "standard",
  "prompt_text": "Текст промпта для анализа"
}
```

**Поля запроса:**

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `request_id` | string | Нет | Идентификатор запроса (автогенерация, если не указан) |
| `user_id` | string | Да | Идентификатор пользователя (для истории, аналитики, лимитов) |
| `source` | string | Нет | Источник: `web`, `telegram`, `n8n`, `cli` (default: `web`) |
| `review_mode` | string | Нет | Режим анализа: `standard`, `detailed` (default: `standard`) |
| `prompt_text` | string | Да | Текст для анализа |

**Response (200 OK):**
```json
{
  "request_id": "req_001",
  "user_id": "user_123",
  "is_prompt": true,
  "purpose": "Создание AI-ассистента для анализа продаж",
  "strengths": [
    "Чётко определена цель",
    "Указана целевая аудитория",
    "Структурированный формат вывода"
  ],
  "weaknesses": [
    "Отсутствуют примеры входных данных",
    "Не указаны ограничения по токенам"
  ],
  "recommendations": [
    {
      "priority": "high",
      "text": "Добавить примеры входных данных и ожидаемых результатов"
    },
    {
      "priority": "medium",
      "text": "Указать ограничения по длине ответа"
    }
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
  "revised_prompt": "Улучшенная редакция промпта...",
  "reason": null,
  "conversion_options": [],
  "metrics": {
    "characters": 450,
    "words": 67,
    "lines": 12,
    "markdown_elements": 3
  },
  "processing_time_ms": 2345
}
```

**Response (текст не является промптом):**
```json
{
  "request_id": "req_002",
  "user_id": "user_456",
  "is_prompt": false,
  "purpose": null,
  "strengths": [],
  "weaknesses": [],
  "recommendations": [],
  "scores": {},
  "quality_level": "not_applicable",
  "revised_prompt": null,
  "reason": "Текст не содержит инструкции для AI. Это обычный текст без задачи или контекста для языковой модели.",
  "conversion_options": [
    "Добавьте задачу: что должен сделать AI?",
    "Укажите контекст: для чего нужен результат?",
    "Определите формат вывода"
  ],
  "metrics": {
    "characters": 120,
    "words": 18,
    "lines": 3
  },
  "processing_time_ms": 856
}
```

**Поля ответа:**

| Поле | Тип | Описание |
|------|-----|----------|
| `request_id` | string | Идентификатор запроса (эхо) |
| `user_id` | string | Идентификатор пользователя |
| `is_prompt` | boolean | Является ли текст промптом |
| `purpose` | string \| null | Назначение промпта (если is_prompt=true) |
| `strengths` | array | Сильные стороны промпта |
| `weaknesses` | array | Слабые стороны промпта |
| `recommendations` | array | Рекомендации по улучшению |
| `scores` | object | Оценки по критериям (0-10) |
| `quality_level` | string | Уровень качества: `excellent`, `good`, `fair`, `poor`, `not_applicable` |
| `revised_prompt` | string \| null | Улучшенная редакция (если is_prompt=true) |
| `reason` | string \| null | Причина, почему текст не является промптом |
| `conversion_options` | array | Варианты преобразования в промпт |
| `metrics` | object | Метрики текста |
| `processing_time_ms` | number | Время обработки в миллисекундах |

**Error Responses:**

```json
// 400 Bad Request
{
  "error": "validation_error",
  "message": "prompt_text is required",
  "details": {}
}

// 500 Internal Server Error
{
  "error": "internal_error",
  "message": "Backend processing failed",
  "details": {}
}

// 503 Service Unavailable
{
  "error": "backend_unavailable",
  "message": "LangFlow API is not responding",
  "details": {}
}
```

---

## 4. UI-сценарии

### 4.1 Telegram Bot

**Архитектура:**
```
Telegram Bot → POST /review → FastAPI → Prompt Review Engine → JSON → человекочитаемый ответ
```

**Минимальный функционал:**
- Принять сообщение пользователя
- Сформировать `user_id = "telegram:{telegram_id}"`
- Установить `source = "telegram"`
- Отправить `prompt_text` в `/review`
- Вернуть краткий результат:
  - `is_prompt`, `quality_level`, `overall_score`
  - 2-3 рекомендации (top priority)
  - При `is_prompt=false` — reason + conversion_options

**Формат ответа в Telegram:**

Если промпт:
```
✅ Это промпт

📋 Назначение: {purpose}
📊 Оценка: {overall_score}/10 ({quality_level})

💪 Сильные стороны:
• {strength_1}
• {strength_2}

⚠️ Рекомендации:
• {rec_1}
• {rec_2}

💡 Улучшенная версия:
{revised_prompt}
```

Если не промпт:
```
❌ Это не промпт для AI

Причина: {reason}

💡 Как превратить в промпт:
1. {conversion_option_1}
2. {conversion_option_2}
```

### 4.2 Web UI

**Архитектура:**
```
Web Form → POST /review → FastAPI → Prompt Review Engine → JSON → результат на странице
```

**Минимальный функционал:**
- Textarea для `prompt_text`
- Скрытый или генерируемый `user_id`/`session_id`
- Установить `source = "web"`
- Кнопка "Проверить промпт"
- Вывод результатов:
  - Назначение промпта
  - Оценки по критериям
  - Рекомендации
  - Улучшенная редакция (или conversion_options)

**Элементы интерфейса:**
- Поле ввода (textarea, min 10 символов)
- Индикатор загрузки
- Блок результатов с tabs/accordion:
  - 📊 Overview (purpose, quality_level, scores)
  - ✅ Strengths
  - ⚠️ Weaknesses
  - 💡 Recommendations
  - 📝 Improved Version (если is_prompt=true)
  - 🔄 Conversion Options (если is_prompt=false)

---

## 5. Production Requirements

### 5.1 Безопасность

| Требование | Реализация |
|------------|------------|
| **HTTPS** | TLS 1.3, сертификат Let's Encrypt |
| **API Key / JWT** | Заголовок `Authorization: Bearer {token}` |
| **CORS Allowlist** | Явный список разрешённых origins |
| **Секреты** | Переменные окружения, `.env` вне git |

**Пример конфигурации CORS:**
```python
ALLOWED_ORIGINS = [
    "https://prompt-review.example.com",
    "https://t.me",
]
```

### 5.2 Надёжность

| Требование | Реализация |
|------------|------------|
| **Валидация** | Pydantic models для request/response |
| **Обработка ошибок** | Graceful degradation при ошибках LLM |
| **Timeout** | Ограничение времени запроса (default: 30s) |
| **Retry** | Экспоненциальный backoff для retry |
| **Health Check** | `/health` endpoint для мониторинга |

### 5.3 Эксплуатация

| Требование | Реализация |
|------------|------------|
| **Logging** | Structured logging (JSON), correlation via `request_id` |
| **Request ID** | Автогенерация UUID, эхо в ответе |
| **User ID** | Обязательно в запросе, логируется |
| **Rate Limiting** | Ограничение запросов на пользователя |
| **Docker** | Контейнеризация, docker-compose |
| **Env Variables** | Конфигурация через `.env` |
| **Monitoring** | Prometheus metrics, health checks |

### 5.4 Переменные окружения

```bash
# Backend configuration
BACKEND_TYPE=langflow|langchain
LANGFLOW_URL=https://langflow.example.com
LANGFLOW_FLOW_ID=abc123
LANGFLOW_API_KEY=your_api_key
LANGCHAIN_MODEL=openai|ollama

# API configuration
API_KEY=your_api_key
CORS_ORIGINS=https://example.com,https://t.me

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Limits
REQUEST_TIMEOUT_SECONDS=30
MAX_PROMPT_LENGTH=10000
RATE_LIMIT_PER_MINUTE=60
```

---

## 6. Состав артефактов PEl06

### 6.1 Обязательные артефакты

| Артефакт | Путь | Назначение |
|----------|------|------------|
| API implementation | `api/main.py` | FastAPI-сервер |
| Requirements | `api/requirements.txt` | Зависимости Python |
| Environment template | `api/.env.example` | Пример конфигурации |
| API documentation | `api/README.md` | Документация API |
| Test cases | `api/tests.md` | Тестовые сценарии |
| Root README | `README.md` | Обновлённое описание кейса |

### 6.2 Скриншоты для отчёта

| Скриншот | Назначение |
|----------|------------|
| FastAPI `/docs` | Интерактивная документация |
| FastAPI `/health` | Health check |
| POST `/review` (промпт) | Анализ промпта |
| POST `/review` (не промпт) | Альтернативная ветка |
| Telegram: отправка промпта | Input в Telegram |
| Telegram: ответ агента | Output в Telegram |
| Web: форма | Форма ввода |
| Web: результат | Результат анализа |

---

## 7. Definition of Done

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

---

## 8. Глоссарий

| Термин | Определение |
|--------|-------------|
| **Prompt Review Engine** | Ядро анализа промптов (LangFlow или LangChain) |
| **Backend Adapter** | Адаптер для вызова конкретного backend |
| **JSON-контракт** | Единый формат ответа для всех сценариев |
| **Quality Level** | Итоговая оценка качества промпта |
| **Review Mode** | Режим анализа: стандартный или детальный |