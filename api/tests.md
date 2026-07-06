# Тестовые сценарии Prompt Review Service

**Дата тестирования:** 2026-07-05
**Backend:** LangChain (OpenAI gpt-4o-mini)
**Статус:** ✅ Все тесты пройдены

---

## 1. Endpoint: GET /

### 1.1. Корневой endpoint

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

**Status:** ✅ PASSED

---

## 2. Endpoint: GET /health

### 2.1. Health check

**Request:**
```http
GET /health
```

**Response:**
```json
{
    "status": "ok",
    "backend": "langchain",
    "backend_available": true
}
```

**Status:** ✅ PASSED

---

## 3. Endpoint: POST /review

### 3.1. Позитивный тест: корректный промпт

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user_001",
    "prompt_text": "Ты — опытный преподаватель Python. Объясни начинающему разработчику, что такое словарь (dict), используя простой пример из реальной жизни. Ответ должен содержать: краткое объяснение, пример кода, типичные ошибки новичков."
}
```

**Response:**
```json
{
    "request_id": "req_1783282301232_cfc24e17",
    "user_id": "test_user_001",
    "is_prompt": true,
    "purpose": "Объяснить начинающему разработчику, что такое словарь в Python с использованием простого примера.",
    "strengths": [
        "Чётко определённая цель объяснения.",
        "Запрос на использование реального примера делает информацию более доступной.",
        "Указание на типичные ошибки помогает избежать распространённых проблем."
    ],
    "weaknesses": [
        "Не указаны конкретные требования к формату ответа.",
        "Отсутствие информации о желаемой длине объяснения.",
        "Неясно, какой уровень детализации требуется для примера кода."
    ],
    "recommendations": [
        {
            "priority": "medium",
            "text": "Уточнить требования к формату ответа (например, текст, код, список)."
        },
        {
            "priority": "medium",
            "text": "Добавить информацию о желаемой длине объяснения и примера кода."
        },
        {
            "priority": "medium",
            "text": "Указать, какие именно типичные ошибки следует рассмотреть."
        }
    ],
    "scores": {
        "clarity": 7,
        "completeness": 5,
        "ambiguity_absence": 6,
        "target_audience_fit": 8,
        "output_format": 4,
        "constraints_quality": 5,
        "missing_assumptions": 6,
        "structure_reusability": 5,
        "overall": 6.0
    },
    "quality_level": "fair",
    "revised_prompt": "Ты — опытный преподаватель Python. Объясни начинающему разработчику, что такое словарь (dict), используя простой пример из реальной жизни. Ответ должен содержать: краткое объяснение (не более 100 слов), пример кода (до 5 строк), типичные ошибки новичков (перечислить 3-5 ошибок). Формат ответа: текст, код, список.",
    "reason": null,
    "conversion_options": [],
    "metrics": {
        "characters": 221,
        "words": 27,
        "lines": 1,
        "non_empty_lines": 1,
        "markdown_headings": 0,
        "bullet_items": 0,
        "numbered_items": 0,
        "markdown_table_lines": 0,
        "xml_tags": 0,
        "code_blocks": 0,
        "max_line_length": 221,
        "avg_line_length": 221
    },
    "processing_time_ms": 10607,
    "notes": []
}
```

**Статус:** ✅ PASSED

**Проверки:**
- [x] `is_prompt: true`
- [x] `purpose` заполнен
- [x] `strengths` содержит элементы
- [x] `weaknesses` содержит элементы
- [x] `recommendations` содержит элементы с priority
- [x] `scores` содержит все 9 критериев
- [x] `quality_level` валидное значение
- [x] `revised_prompt` заполнен
- [x] `metrics` содержит все поля
- [x] `processing_time_ms` > 0

---

### 3.2. Негативный тест: обычный текст (не промпт)

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user_002",
    "prompt_text": "Привет, как дела? Что нового?"
}
```

**Response:**
```json
{
    "request_id": "req_1783282318780_d29c8761",
    "user_id": "test_user_002",
    "is_prompt": false,
    "purpose": null,
    "strengths": [],
    "weaknesses": [],
    "recommendations": [],
    "scores": null,
    "quality_level": "not_applicable",
    "revised_prompt": null,
    "reason": "Обычный разговорный текст без инструкции или описания задачи.",
    "conversion_options": [
        "Добавьте ролевую инструкцию (например: \"Ты — ...\")",
        "Укажите ожидаемый формат результата",
        "Опишите конкретную задачу"
    ],
    "metrics": {
        "characters": 29,
        "words": 5,
        "lines": 1,
        "non_empty_lines": 1,
        "markdown_headings": 0,
        "bullet_items": 0,
        "numbered_items": 0,
        "markdown_table_lines": 0,
        "xml_tags": 0,
        "code_blocks": 0,
        "max_line_length": 29,
        "avg_line_length": 29
    },
    "processing_time_ms": 911,
    "notes": []
}
```

**Статус:** ✅ PASSED

**Проверки:**
- [x] `is_prompt: false`
- [x] `purpose: null`
- [x] `strengths: []`
- [x] `weaknesses: []`
- [x] `recommendations: []`
- [x] `scores: null`
- [x] `quality_level: "not_applicable"`
- [x] `revised_prompt: null`
- [x] `reason` заполнен
- [x] `conversion_options` содержит элементы

---

## 4. Граничные случаи

### 4.1. Пустой текст (min_length violation)

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user_003",
    "prompt_text": ""
}
```

**Response:**
```json
{
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["body", "prompt_text"],
            "msg": "String should have at least 10 characters",
            "input": "",
            "ctx": {
                "min_length": 10
            }
        }
    ]
}
```

**Статус:** ✅ PASSED (422 Unprocessable Entity)

---

### 4.2. Минимальная длина (10 символов)

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user_003",
    "prompt_text": "1234567890"
}
```

**Response:** Принят, обработан как не-промпт.

**Статус:** ✅ PASSED

---

### 4.3. Длинный текст (8500 символов)

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user_004",
    "prompt_text": "Тестовый промпт. Тестовый промпт. ..." (8500 chars)
}
```

**Response:** Принят, обработан. Классифицирован как не-промпт (повторяющиеся фразы).

**Статус:** ✅ PASSED

---

## 5. Обработка ошибок

### 5.1. Некорректный JSON

**Request:**
```http
POST /review
Content-Type: application/json

{invalid json
```

**Response:**
```json
{
    "detail": [
        {
            "type": "json_invalid",
            "loc": ["body", 1],
            "msg": "JSON decode error",
            "input": {},
            "ctx": {
                "error": "Expecting property name enclosed in double quotes"
            }
        }
    ]
}
```

**Статус:** ✅ PASSED

---

### 5.2. Отсутствует обязательное поле user_id

**Request:**
```http
POST /review
Content-Type: application/json

{
    "prompt_text": "Тестовый промпт"
}
```

**Response:**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "user_id"],
            "msg": "Field required",
            "input": {
                "prompt_text": "Тестовый промпт"
            }
        }
    ]
}
```

**Статус:** ✅ PASSED

---

### 5.3. Отсутствует обязательное поле prompt_text

**Request:**
```http
POST /review
Content-Type: application/json

{
    "user_id": "test_user"
}
```

**Response:**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "prompt_text"],
            "msg": "Field required"
        }
    ]
}
```

**Статус:** ✅ PASSED

---

## 6. Swagger UI и OpenAPI

### 6.1. Swagger UI

**URL:** http://localhost:8000/docs

**Статус:** ✅ PASSED

**Проверки:**
- [x] Swagger UI доступен
- [x] Отображаются все endpoints
- [x] Можно протестировать interactively

---

### 6.2. OpenAPI Schema

**URL:** http://localhost:8000/openapi.json

**Response:**
```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "Prompt Review Service",
        "version": "1.0.0"
    },
    "paths": {
        "/": {...},
        "/health": {...},
        "/review": {...}
    }
}
```

**Статус:** ✅ PASSED

---

## 7. JSON-контракт

### 7.1. Совместимость с SPEC.md

**Проверено:**
- [x] PromptReviewRequest: все поля соответствуют спецификации
- [x] PromptReviewResponse: все поля соответствуют спецификации
- [x] QualityLevel enum: excellent, good, fair, poor, not_applicable
- [x] Source enum: web, telegram, n8n, cli
- [x] ReviewMode enum: standard, detailed

### 7.2. Поля PromptReviewResponse

| Поле | Тип | Обязательное | Проверено |
|------|-----|--------------|-----------|
| request_id | string | ✅ | ✅ |
| user_id | string | ✅ | ✅ |
| is_prompt | boolean | ✅ | ✅ |
| purpose | string \| null | ❌ | ✅ |
| strengths | array | ❌ | ✅ |
| weaknesses | array | ❌ | ✅ |
| recommendations | array | ❌ | ✅ |
| scores | object \| null | ❌ | ✅ |
| quality_level | string | ✅ | ✅ |
| revised_prompt | string \| null | ❌ | ✅ |
| reason | string \| null | ❌ | ✅ |
| conversion_options | array | ❌ | ✅ |
| metrics | object | ✅ | ✅ |
| processing_time_ms | number | ✅ | ✅ |
| notes | array | ❌ | ✅ |

---

## 8. Health Check

### 8.1. Проверка backend_available

**Request:**
```http
GET /health
```

**Response (с OPENAI_API_KEY):**
```json
{
    "status": "ok",
    "backend": "langchain",
    "backend_available": true
}
```

**Response (без API ключа):**
```json
{
    "status": "ok",
    "backend": "langchain",
    "backend_available": false
}
```

**Статус:** ✅ PASSED

---

## 9. Логирование

### 9.1. Структурированное логирование (JSON)

**Формат лога:**
```json
{
    "timestamp": "2026-07-05T20:09:09.635704",
    "level": "INFO",
    "logger": "app.main",
    "message": "Review request received",
    "request_id": "req_1783282149635_f2a44fb0",
    "user_id": "test_user"
}
```

**Статус:** ✅ PASSED

---

## 10. Производительность

### 10.1. Время обработки

| Сценарий | Время (ms) |
|----------|------------|
| Корректный промпт | ~10000 (LLM) |
| Не промпт | ~1000 (LLM) |
| GET / | <10 |
| GET /health | <10 |

**Примечание:** Время обработки зависит от LLM (OpenAI API).

---

## Итоговая таблица тестов

| # | Тест | Статус |
|---|------|--------|
| 1 | GET / | ✅ PASSED |
| 2 | GET /health | ✅ PASSED |
| 3 | POST /review (валидный промпт) | ✅ PASSED |
| 4 | POST /review (не промпт) | ✅ PASSED |
| 5 | Пустой текст | ✅ PASSED |
| 6 | Длинный текст | ✅ PASSED |
| 7 | Некорректный JSON | ✅ PASSED |
| 8 | Отсутствует user_id | ✅ PASSED |
| 9 | Отсутствует prompt_text | ✅ PASSED |
| 10 | Swagger UI | ✅ PASSED |
| 11 | OpenAPI schema | ✅ PASSED |
| 12 | JSON-контракт | ✅ PASSED |
| 13 | Health check | ✅ PASSED |
| 14 | Логирование | ✅ PASSED |

**Всего тестов:** 14
**Пройдено:** 14
**Не пройдено:** 0

---

## Рекомендации

1. **Тестирование с LangFlow:** Необходимо протестировать с `BACKEND_TYPE=langflow` при наличии доступного LangFlow сервера.

2. **Тестирование производительности:** При нагрузочном тестировании учитывать время ответа LLM.

3. **Мониторинг:** Добавить метрики Prometheus для production.

---

**Тестирование завершено:** 2026-07-05
**Тестировщик:** Claude (LangChainAdapter + OpenAI)

---

## 11. Дополнительное тестирование: LangFlowAdapter

**Дата тестирования:** 2026-07-05
**Backend:** LangFlow (https://langflow.alex-n8n.site)
**Flow ID:** eaa36f47-604c-4c62-902b-d4c84ffde61a

### 11.1. Предварительные шаги

1. **Настройка окружения:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp ../infra/.env .env
   ```

2. **Конфигурация .env:**
   ```bash
   BACKEND_TYPE=langflow
   LANGFLOW_URL=https://langflow.alex-n8n.site
   LANGFLOW_FLOW_ID=eaa36f47-604c-4c62-902b-d4c84ffde61a
   LANGFLOW_API_KEY=sk-...
   ```

3. **Запуск сервера:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
   ```

### 11.2. Тестовые сценарии

#### 11.2.1. POST /review — Валидный промпт

**Request:**
```bash
curl -X POST http://localhost:8765/review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "prompt_text": "Напиши функцию на Python, которая принимает список чисел и возвращает их сумму"
  }'
```

**Response:**
```json
{
  "request_id": "req_1783289465775_26b687a7",
  "user_id": "test-user-001",
  "is_prompt": true,
  "purpose": "Написать функцию на Python, принимающую список чисел и возвращающую их сумму.",
  "strengths": [
    "Понятная и конкретная задача.",
    "Минимальный набор требований без лишних ограничений."
  ],
  "weaknesses": [
    "Не указан формат вывода: только код или код с пояснением.",
    "Не уточнено, нужно ли учитывать пустой список, нечисловые элементы и типы чисел.",
    "Не задано имя функции, стиль оформления и требования к тестовому примеру."
  ],
  "recommendations": [
    {
      "priority": "medium",
      "text": "Уточнить ожидаемый формат ответа: только функция, либо функция с кратким пояснением."
    },
    {
      "priority": "medium",
      "text": "Добавить поведение для пустого списка и некорректных элементов."
    },
    {
      "priority": "medium",
      "text": "При необходимости задать имя функции и требования к примерам использования."
    }
  ],
  "scores": {
    "clarity": 8,
    "completeness": 5,
    "ambiguity_absence": 6,
    "target_audience_fit": 9,
    "output_format": 4,
    "constraints_quality": 5,
    "missing_assumptions": 5,
    "structure_reusability": 7,
    "overall": 6.125
  },
  "quality_level": "good",
  "revised_prompt": "Напиши на Python функцию `sum_numbers`, которая принимает список чисел и возвращает их сумму. Предположи, что список содержит только числа. Верни только код функции без дополнительных пояснений.",
  "processing_time_ms": 3271
}
```

**Статус:** ✅ PASSED

---

#### 11.2.2. POST /review — Не промпт

**Request:**
```bash
curl -X POST http://localhost:8765/review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-002",
    "prompt_text": "Привет, как дела?"
  }'
```

**Response:**
```json
{
  "request_id": "req_1783289472608_f9ee604d",
  "user_id": "test-user-002",
  "is_prompt": false,
  "reason": "Сообщение является обычным приветствием и не содержит инструкции или задачи для языковой модели.",
  "conversion_options": [
    "Промпт для анализа: «Проанализируй следующий промпт: ...»",
    "Промпт для ответа: «Ответь на приветствие пользователя дружелюбно и кратко.»"
  ],
  "processing_time_ms": 1742
}
```

**Статус:** ✅ PASSED

---

#### 11.2.3. Валидация: Пустой текст

**Request:**
```bash
curl -X POST http://localhost:8765/review \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-003", "prompt_text": ""}'
```

**Response:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "prompt_text"],
      "msg": "String should have at least 10 characters"
    }
  ]
}
```

**Статус:** ✅ PASSED (422 Unprocessable Entity)

---

#### 11.2.4. Валидация: Слишком длинный текст

**Request:**
```bash
# 10001+ символов
curl -X POST http://localhost:8765/review \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user-004", "prompt_text": "x...10001 chars...x"}'
```

**Response:**
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "prompt_text"],
      "msg": "String should have at most 10000 characters"
    }
  ]
}
```

**Статус:** ✅ PASSED (422 Unprocessable Entity)

---

### 11.3. Исправленные проблемы

#### 11.3.1. Ошибка парсинга LangFlow ответа

**Проблема:**
```
LangFlow unexpected error: 'str' object has no attribute 'get'
```

**Root Cause:**
LangFlow возвращает `recommendations` как массив строк, а не массив объектов:
```json
"recommendations": [
  "Уточнить формат ответа...",
  "Явно указать...",
  "..."
]
```

Код ожидал массив объектов с полями `priority` и `text`.

**Решение:**
Обновлён парсинг `recommendations` в `LangFlowAdapter._parse_langflow_response()`:
```python
# recommendations может быть списком строк или списком объектов
recommendations = []
for r in recommendations_data:
    if isinstance(r, dict):
        recommendations.append(Recommendation(
            priority=r.get("priority", "medium"),
            text=r.get("text", str(r))
        ))
    elif isinstance(r, str):
        recommendations.append(Recommendation(
            priority="medium",
            text=r
        ))
```

**Файл:** `app/adapters/langflow.py`

---

#### 11.3.2. Ошибка валидации Settings

**Проблема:**
```
ValidationError: Extra inputs are not permitted
```

**Root Cause:**
Файл `.env` содержит переменные для LangFlow infra (POSTGRES_PASSWORD, LANGFLOW_SECRET_KEY, etc.), которые не определены в Settings.

**Решение:**
Добавлено `extra = "ignore"` в Settings.Config:
```python
class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    case_sensitive = False
    extra = "ignore"  # Игнорировать лишние переменные из .env
```

**Файл:** `app/config.py`

---

### 11.4. Производительность LangFlowAdapter

| Сценарий | Время (ms) |
|----------|------------|
| Валидный промпт | ~3271 |
| Не промпт | ~1742 |
| GET / | <10 |
| GET /health | <10 |

**Примечание:** LangFlow работает быстрее LangChain (OpenAI) — ~3 сек vs ~10 сек.

---

### 11.5. Сводная таблица LangFlowAdapter

| # | Тест | Статус |
|---|------|--------|
| 1 | GET / | ✅ PASSED |
| 2 | GET /health | ✅ PASSED |
| 3 | POST /review (валидный промпт) | ✅ PASSED |
| 4 | POST /review (не промпт) | ✅ PASSED |
| 5 | Пустой текст | ✅ PASSED |
| 6 | Слишком длинный текст | ✅ PASSED |
| 7 | Отсутствует user_id | ✅ PASSED |
| 8 | Отсутствует prompt_text | ✅ PASSED |
| 9 | Swagger UI | ✅ PASSED |
| 10 | OpenAPI schema | ✅ PASSED |

**Всего тестов:** 10
**Пройдено:** 10
**Не пройдено:** 0

---

**Тестирование LangFlowAdapter завершено:** 2026-07-05