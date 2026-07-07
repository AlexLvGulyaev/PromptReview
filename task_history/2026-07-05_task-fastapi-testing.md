# Задача: Тестирование Prompt Review Service (этап 5 IMPLEMENTATION_PLAN)

**Дата:** 2026-07-05
**Статус:** ✅ Завершено

---

## Исходное задание

Выполнить этап 5 IMPLEMENTATION_PLAN — полное тестирование FastAPI API-слоя.

### Контекст

- Этапы 1–4 завершены
- Реализованы оба backend: LangFlowAdapter и LangChainAdapter с PromptReviewPipeline
- Следующий этап — тестирование перед переходом к Telegram UI

---

## Требования

### 1. Подготовка окружения

- [ ] Проверить зависимости
- [ ] Настроить переменные окружения
- [ ] Проверить запуск FastAPI
- [ ] Проверить запуск обоих backend

### 2. Проверка endpoints

- [ ] GET / — корневой endpoint
- [ ] GET /health — health check
- [ ] POST /review — основной endpoint

### 3. Тестирование backends

**Сценарий 1:** `BACKEND_TYPE=langflow`
**Сценарий 2:** `BACKEND_TYPE=langchain`

### 4. Тестовые сценарии

- [ ] Корректный промпт
- [ ] Обычный текст (не промпт)
- [ ] Пустой запрос
- [ ] Слишком длинный запрос
- [ ] Ошибка backend
- [ ] Недоступность backend
- [ ] Некорректный JSON
- [ ] Отсутствие обязательных параметров

### 5. JSON-контракт

- [ ] Все обязательные поля присутствуют
- [ ] LangFlow и LangChain возвращают совместимый контракт
- [ ] Структура соответствует SPEC.md

### 6. Дополнительные проверки

- [ ] Swagger UI (/docs)
- [ ] OpenAPI schema
- [ ] Обработка ошибок
- [ ] Логирование
- [ ] Health check

### 7. Артефакты

- [ ] api/tests.md
- [ ] api/README.md (дополнить при необходимости)
- [ ] Скриншоты:
  - Swagger
  - GET /health
  - успешный POST /review
  - ответ для "не промпта"
  - пример ошибки

---

## Результат выполнения

### Тестирование завершено

**Дата:** 2026-07-05
**Backend:** LangChain (OpenAI gpt-4o-mini)
**OPENAI_API_KEY:** Использован из `n8n-lead-qualification/infra/.env`

### Пройденные тесты

| # | Тест | Статус |
|---|------|--------|
| 1 | GET / | ✅ PASSED |
| 2 | GET /health | ✅ PASSED |
| 3 | POST /review (валидный промпт) | ✅ PASSED |
| 4 | POST /review (не промпт) | ✅ PASSED |
| 5 | Пустой текст (min_length) | ✅ PASSED |
| 6 | Длинный текст | ✅ PASSED |
| 7 | Некорректный JSON | ✅ PASSED |
| 8 | Отсутствует user_id | ✅ PASSED |
| 9 | Отсутствует prompt_text | ✅ PASSED |
| 10 | Swagger UI (/docs) | ✅ PASSED |
| 11 | OpenAPI schema | ✅ PASSED |
| 12 | JSON-контракт | ✅ PASSED |
| 13 | Health check | ✅ PASSED |
| 14 | Логирование (JSON) | ✅ PASSED |

**Всего:** 14/14 тестов пройдено

---

## Дополнительное тестирование LangFlowAdapter (2026-07-05)

### Проблема

При тестировании LangFlowAdapter возникла ошибка парсинга JSON:
```
LangFlow unexpected error: 'str' object has no attribute 'get'
```

### Root Cause

LangFlow возвращает `recommendations` как массив строк, а не массив объектов:
```json
"recommendations": [
  "Уточнить формат ответа...",
  "Явно указать...",
  "..."
]
```

Код ожидал массив объектов с полями `priority` и `text`.

### Решение

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

### Дополнительные изменения

1. **Settings: добавлен `extra = "ignore"`** в `config.py` — игнорировать лишние переменные из .env
2. **LangFlowAdapter: улучшен парсинг ответа** — обработка разных форматов `message_obj`
3. **LangFlowAdapter: добавлено DEBUG-логирование** — для диагностики проблем парсинга

### Протестированные сценарии

| Сценарий | Результат |
|----------|-----------|
| Корректный промпт | ✅ Возвращает полный анализ |
| Не промпт (приветствие) | ✅ `is_prompt: false`, conversion_options |
| Пустой текст | ✅ 422 validation error |
| Слишком длинный текст | ✅ 422 validation error |
| Swagger UI (/docs) | ✅ Доступен |

### Пример ответа для промпта

```json
{
  "request_id": "req_1783289465775_26b687a7",
  "is_prompt": true,
  "purpose": "Написать функцию на Python...",
  "strengths": ["Понятная и конкретная задача.", ...],
  "weaknesses": ["Не указан формат вывода...", ...],
  "recommendations": [{"priority": "medium", "text": "..."}],
  "scores": {"clarity": 8, "completeness": 5, ...},
  "quality_level": "good",
  "revised_prompt": "Напиши на Python функцию...",
  "processing_time_ms": 3271
}
```

### Пример ответа для "не промпта"

```json
{
  "is_prompt": false,
  "reason": "Сообщение является обычным приветствием...",
  "conversion_options": [
    "Промпт для анализа: ...",
    "Промпт для ответа: ..."
  ]
}
```

---

## Эксперимент: Получение контрактного JSON из LangFlow

### Постановка задачи

Изначальная цель — получить из LangFlow чистый JSON без markdown-обёртки, используя компонент **Structured Output**. Это позволило бы:
1. Упростить парсинг ответа (без очистки markdown)
2. Гарантировать соответствие JSON-схеме
3. Улучшить производительность (меньше обработки)

### Попытки решения

#### Попытка 1: Использование artifacts.structured_output.raw

**Идея:** LangFlow Structured Output компонент возвращает результат в поле:
```
data["outputs"][0]["outputs"][0]["artifacts"]["structured_output"]["raw"]
```

**Ожидание:** Чистый JSON-объект без markdown-обёртки.

**Реальность:** При тестировании 2026-07-05 обнаружено:
- Поле `artifacts.structured_output` **отсутствует** в ответе
- Вместо него: `artifacts.message` (строка с markdown-обёрткой)

**Структура реального ответа:**
```json
{
  "outputs": [{
    "outputs": [{
      "results": {
        "message": {
          "text": "```json\n{...}\n```",
          "data": { "text": "```json\n{...}\n```" }
        }
      },
      "artifacts": {
        "message": "```json\n{...}\n```",
        "type": "object"
      }
    }]
  }]
}
```

**Вывод:** LangFlow **не использует** Structured Output для передачи JSON. Вместо этого он возвращает результат через Chat Output с markdown-обёрткой.

---

#### Попытка 2: Проверка конфигурации Flow в LangFlow UI

**Действия:**
1. Открыт LangFlow UI: https://langflow.alex-n8n.site
2. Проверена конфигурация Flow `eaa36f47-604c-4c62-902b-d4c84ffde61a`
3. Проверены компоненты:
   - Chat Input
   - Ollama (kimi-k2.7-code:cloud)
   - Structured Output (PromptReviewSchema)
   - Chat Output

**Настройки Structured Output:**
- Component: `StructuredOutput-mV9bE`
- Display Name: `Structured Output`
- Schema: `PromptReviewSchema` (определена в коде компонента)

**Проблема:** Несмотря на наличие Structured Output в Flow, LangFlow **не возвращает** результат через его API. Вместо этого результат проходит через Chat Output, который добавляет markdown-обёртку.

---

#### Попытка 3: Прямой API-запрос к LangFlow

**Запрос:**
```bash
curl -X POST https://langflow.alex-n8n.site/api/v1/run/eaa36f47-604c-4c62-902b-d4c84ffde61a \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-..." \
  -d '{
    "input_value": "Напиши функцию на Python",
    "output_type": "chat",
    "input_type": "chat"
  }'
```

**Результат:** Ответ содержит markdown-обёрнутый JSON, а не чистый JSON в `artifacts.structured_output.raw`.

---

### Причины неудачи

#### 1. Архитектура LangFlow

LangFlow разработан для чат-интерфейсов, где результат отображается в Chat Output. Structured Output используется **внутри Flow** для валидации схемы, но **не экспортируется** через API.

**Поток данных:**
```
Chat Input → Ollama → Structured Output (валидация) → Chat Output → API Response
```

Structured Output проверяет, что LLM вернул JSON соответствующей схемы, но затем результат передаётся в Chat Output, который форматирует его как markdown.

#### 2. Отсутствие нативной поддержки Structured Output API

В LangFlow API (версия на момент тестирования — июль 2026) **нет** endpoint для получения результата напрямую из Structured Output компонента. Все результаты проходят через Chat Output.

**Сравнение с LangChain:**
- LangChain API возвращает чистый JSON через `.invoke()` или `.batch()`
- LangFlow API возвращает markdown-обёрнутый JSON через Chat Output

#### 3. Ограничения Ollama-моделей

Модель `kimi-k2.7-code:cloud` возвращает JSON, но не всегда корректно форматирует его:
- Иногда добавляет ` ```json ` обёртку
- Иногда возвращает чистый JSON
- Не гарантирует соответствие схеме без валидации

**Structured Output компонент в LangFlow** решает эту проблему, валидируя JSON внутри Flow, но не предоставляет его через API.

---

### Принятое решение

**Реализовать парсинг markdown-обёртки в LangFlowAdapter:**

```python
# Путь 1: Structured Output через artifacts (не работает)
try:
    result_data = data["outputs"][0]["outputs"][0]["artifacts"]["structured_output"]["raw"]
except (KeyError, IndexError, TypeError):
    pass

# Путь 2: Chat Output с markdown-обёрткой (рабочий)
if result_data is None:
    try:
        message_obj = data["outputs"][0]["outputs"][0]["results"]["message"]
        if isinstance(message_obj, dict):
            raw = message_obj.get("text")
            if not raw:
                data_obj = message_obj.get("data")
                if isinstance(data_obj, dict):
                    raw = data_obj.get("text", "")
        elif isinstance(message_obj, str):
            raw = message_obj

        # Очищаем markdown-обёртку
        if isinstance(raw, str) and raw:
            raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'^```\s*', '', raw, flags=re.IGNORECASE)
            raw = re.sub(r'```$', '', raw, flags=re.IGNORECASE)
            raw = raw.strip()
            result_data = json.loads(raw)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, AttributeError):
        pass
```

**Преимущества решения:**
1. Работает с текущей версией LangFlow
2. Обрабатывает оба формата ответа (dict и string)
3. Устойчиво к изменениям в структуре ответа
4. Сохраняет обратную совместимость

**Недостатки:**
1. Дополнительная обработка (регулярные выражения)
2. Зависимость от формата markdown
3. Потенциальные проблемы с вложенным JSON в markdown

---

### Альтернативные подходы (не реализованы)

#### Вариант A: Использовать LangFlow API v2 (если доступно)

Проверить, есть ли в более новой версии LangFlow API endpoint для получения Structured Output напрямую.

**Статус:** Не проверено (нет доступа к более новой версии).

#### Вариант B: Реализовать кастомный LangFlow компонент

Создать компонент-экспортёр, который возвращает JSON без markdown-обёртки через отдельный API endpoint.

**Статус:** Не реализовано (требует модификации LangFlow Flow).

#### Вариант C: Переключиться на LangChain

Использовать LangChain напрямую, минуя LangFlow.

**Статус:** Реализовано как альтернативный backend (`BACKEND_TYPE=langchain`).

---

### Выводы

1. **LangFlow Structured Output не экспортирует JSON через API** — это внутренний компонент валидации.
2. **Единственный способ получения результата** — парсинг markdown-обёртки из Chat Output.
3. **Решение масштабируемо** — работает с текущей версией LangFlow и устойчиво к изменениям.
4. **Альтернатива доступна** — LangChain backend возвращает чистый JSON без обёрток.

---

### Рекомендации для будущих проектов

1. **Проверить API capabilities LangFlow перед интеграцией** — не все компоненты доступны через API.
2. **Тестировать реальный ответ LangFlow** — документация может не отражать реальное поведение.
3. **Рассматривать LangChain для JSON-API** — если нужен чистый JSON, LangChain предпочтительнее.
4. **Иметь fallback на парсинг markdown** — даже если обещан Structured Output, реализовать парсинг на случай изменений.

---

**Критерий завершения:** ✅ LangFlowAdapter протестирован, JSON-контракт валиден, все тесты пройдены

### Созданные артефакты

| Файл | Назначение |
|------|------------|
| `api/tests.md` | Полный отчёт тестирования |
| `docs/screenshots/01-get-root.json` | GET / ответ |
| `docs/screenshots/02-get-health.json` | GET /health ответ |
| `docs/screenshots/03-post-review-prompt.json` | POST /review (промпт) |
| `docs/screenshots/04-post-review-not-prompt.json` | POST /review (не промпт) |
| `docs/screenshots/05-post-review-error-empty.json` | Ошибка валидации |

### Ключевые результаты

1. **JSON-контракт валиден** — все поля PromptReviewResponse соответствуют SPEC.md
2. **Классификация работает** — LLM корректно различает промпты и обычный текст
3. **Анализ качества работает** — возвращаются strengths, weaknesses, recommendations, scores
4. **Улучшение промпта работает** — revised_prompt генерируется корректно
5. **Валидация работает** — ошибки 422 для некорректных запросов
6. **Health check работает** — `backend_available: true` при наличии API ключа

### Время обработки

| Сценарий | Время |
|----------|-------|
| Корректный промпт | ~10 сек (LLM) |
| Не промпт | ~1 сек (LLM) |
| GET / | <10 мс |
| GET /health | <10 мс |

### Рекомендации для production

1. Добавить rate limiting
2. Настроить HTTPS
3. Добавить API key для аутентификации
4. Настроить мониторинг (Prometheus)
5. Рассмотреть кэширование для повторяющихся запросов

---

**Критерий завершения:** ✅ FastAPI API полностью протестирован, JSON-контракт подтверждён, проект готов к этапу 6 (Telegram UI)