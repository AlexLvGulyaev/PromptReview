# API_CONTRACT.md — Prompt Review Service API Contract

**Версия:** 1.0.0
**Дата:** 2026-07-07
**Статус:** Утверждено

---

## Назначение

Этот документ описывает **логический контракт** Prompt Review Service API.

**Source of Truth для валидации:**
- Pydantic-модели: `api/app/schemas.py`
- OpenAPI спецификация: доступна на `/docs` и `/redoc`

**Этот документ описывает:**
- Структуру запроса и ответа
- Допустимые перечисления (enums)
- Семантику полей
- Правила валидации
- Обратную совместимость

**Этот документ НЕ описывает:**
- HTTP-заголовки (см. OpenAPI)
- Коды ответов (см. OpenAPI)
- Формат ошибок (см. OpenAPI)

---

## Endpoint: POST /review

### Запрос: PromptReviewRequest

**Source of Truth:** `api/app/schemas.py`, класс `PromptReviewRequest`.

#### Обязательные поля

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `prompt_text` | string | Текст для анализа | min_length=10, max_length=10000 |
| `user_id` | string | Идентификатор пользователя | min_length=1 |

#### Опциональные поля

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `request_id` | string | Автогенерация | Идентификатор запроса |
| `source` | enum | `"web"` | Источник запроса |
| `review_mode` | enum | `"standard"` | Режим анализа |

#### Enum: Source

**Source of Truth:** `api/app/schemas.py`, класс `Source`.

```python
class Source(str, Enum):
    WEB = "web"
    TELEGRAM = "telegram"
    N8N = "n8n"
    CLI = "cli"
```

**Допустимые значения:**
- `"web"` — запрос через Web UI
- `"telegram"` — запрос через Telegram Bot
- `"n8n"` — запрос через n8n workflow
- `"cli"` — запрос через CLI

**Семантика:** Указывает источник запроса. Может использоваться для аналитики, логирования, маршрутизации.

---

#### Enum: ReviewMode

**Source of Truth:** `api/app/schemas.py`, класс `ReviewMode`.

```python
class ReviewMode(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
```

**Допустимые значения:**
- `"standard"` — стандартный анализ
- `"detailed"` — детальный анализ

**Семантика:** Определяет глубину анализа. В режиме `"detailed"` могут использоваться дополнительные критерии оценки.

**Важно:** В текущей реализации оба режима используют один и тот же конвейер. Различие может быть добавлено в будущих версиях.

---

### Ответ: PromptReviewResponse

**Source of Truth:** `api/app/schemas.py`, класс `PromptReviewResponse`.

#### Общие поля (всегда присутствуют)

| Поле | Тип | Описание |
|------|-----|----------|
| `request_id` | string | Идентификатор запроса |
| `user_id` | string | Идентификатор пользователя |
| `is_prompt` | boolean | Является ли текст промптом |
| `quality_level` | enum | Уровень качества промпта |
| `metrics` | object | Метрики текста |
| `processing_time_ms` | integer | Время обработки в миллисекундах |
| `notes` | array<string> | Дополнительные заметки |

---

#### Поля для `is_prompt = true`

| Поле | Тип | Описание |
|------|-----|----------|
| `purpose` | string \| null | Назначение промпта |
| `strengths` | array<string> | Сильные стороны промпта |
| `weaknesses` | array<string> | Слабые стороны промпта |
| `recommendations` | array<Recommendation> | Рекомендации по улучшению |
| `scores` | object \| null | Оценки по критериям |
| `revised_prompt` | string \| null | Улучшенная редакция промпта |

---

#### Поля для `is_prompt = false`

| Поле | Тип | Описание |
|------|-----|----------|
| `reason` | string \| null | Причина, почему текст не является промптом |
| `conversion_options` | array<string> | Варианты преобразования в промпт |

---

#### Enum: QualityLevel

**Source of Truth:** `api/app/schemas.py`, класс `QualityLevel`.

```python
class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NOT_APPLICABLE = "not_applicable"
```

**Допустимые значения:**
- `"excellent"` — отличный промпт (overall >= 9)
- `"good"` — хороший промпт (7 <= overall < 9)
- `"fair"` — средний промпт (5 <= overall < 7)
- `"poor"` — плохой промпт (3 <= overall < 5)
- `"not_applicable"` — текст не является промптом (overall < 3)

**Семантика:** Общая оценка качества промпта. Для `is_prompt=false` всегда `"not_applicable"`.

**Соответствие overall:**
- `"excellent"`: `overall >= 9`
- `"good"`: `7 <= overall < 9`
- `"fair"`: `5 <= overall < 7`
- `"poor"`: `3 <= overall < 5`
- `"not_applicable"`: `overall < 3` или текст не является промптом

**⚠️ ВАЖНО:** Это **единственный** источник допустимых значений `quality_level`. Все остальные документы и реализации должны ссылаться на этот enum.

---

#### Объект: Recommendation

**Source of Truth:** `api/app/schemas.py`, класс `Recommendation`.

```python
class Recommendation(BaseModel):
    priority: str  # "high" | "medium" | "low"
    text: str
```

**Поля:**
- `priority` — приоритет рекомендации (`"high"`, `"medium"`, `"low"`)
- `text` — текст рекомендации

---

#### Объект: PromptScores

**Source of Truth:** `api/app/schemas.py`, класс `PromptScores`.

```python
class PromptScores(BaseModel):
    clarity: int              # 0-10, понятность постановки задачи
    completeness: int         # 0-10, полнота требований
    ambiguity_absence: int    # 0-10, отсутствие неоднозначностей
    target_audience_fit: int  # 0-10, соответствие целевой аудитории
    output_format: int        # 0-10, формат ожидаемого результата
    constraints_quality: int  # 0-10, качество ограничений
    missing_assumptions: int  # 0-10, наличие недостающих предположений
    structure_reusability: int # 0-10, структурированность и воспроизводимость
    overall: float           # 0-10, интегральная оценка
```

**Семантика:**
- Каждая оценка — число от 0 до 10
- `overall` — средневзвешенная оценка (может быть дробной)
- Для `is_prompt=false` поле `scores` равно `null`

---

#### Объект: PromptMetrics

**Source of Truth:** `api/app/schemas.py`, класс `PromptMetrics`.

```python
class PromptMetrics(BaseModel):
    characters: int           # Количество символов
    words: int               # Количество слов
    lines: int               # Количество строк
    non_empty_lines: int     # Количество непустых строк
    markdown_headings: int    # Количество заголовков markdown
    bullet_items: int        # Количество маркированных списков
    numbered_items: int      # Количество нумерованных списков
    markdown_table_lines: int # Количество строк таблиц
    xml_tags: int            # Количество XML-тегов
    code_blocks: int         # Количество блоков кода
    max_line_length: int     # Максимальная длина строки
    avg_line_length: int     # Средняя длина строки
```

**Семантика:** Инструментально рассчитанные метрики промпта. Вычисляются без использования LLM.

---

## Ветвление ответа

### Логика

Ответ ветвится в зависимости от значения `is_prompt`:

```
if is_prompt == true:
    return {
        purpose: "...",
        strengths: [...],
        weaknesses: [...],
        recommendations: [...],
        scores: {...},
        quality_level: "excellent" | "good" | "fair" | "poor",
        revised_prompt: "...",
        reason: null,
        conversion_options: []
    }

if is_prompt == false:
    return {
        purpose: null,
        strengths: [],
        weaknesses: [],
        recommendations: [],
        scores: null,
        quality_level: "not_applicable",
        revised_prompt: null,
        reason: "...",
        conversion_options: [...]
    }
```

### Классификация

**Критерий:** Текст считается промптом, если он содержит:
- Ролевые инструкции ("Ты —...", "Act as...")
- Описание задачи или действий
- Указание формата результата
- Условия и ограничения
- Примеры или шаблоны

**Не считается промптом:**
- Обычный разговорный текст
- Вопрос без контекста задачи
- Описание ситуации без инструкции
- Повествовательный текст
- Фактическое утверждение

**Source of Truth:** `api/app/pipeline/prompts.py`, `CLASSIFIER_PROMPT`.

---

## Обратная совместимость

### Принципы

1. **Добавление полей:** Разрешено без увеличения версии API.
2. **Удаление полей:** Запрещено без увеличения версии API.
3. **Изменение типов:** Запрещено без увеличения версии API.
4. **Изменение enum:** Разрешено добавление новых значений, запрещено удаление.

### Версионирование

- Текущая версия: `1.0.0`
- Версия указывается в заголовке ответа: `X-API-Version: 1.0.0`

---

## Соответствие overall и quality_level

**Source of Truth для всех реализаций (LangFlow, LangChain, n8n).**

### Правило соответствия

| overall | quality_level | Семантика |
|---------|---------------|-----------|
| >= 9.0 | `excellent` | Отличный промпт |
| 7.0 - 8.9 | `good` | Хороший промпт |
| 5.0 - 6.9 | `fair` | Рабочий промпт |
| 3.0 - 4.9 | `poor` | Слабый промпт |
| < 3.0 | `not_applicable` | Текст не является промптом |

### Обоснование

**Порядок выставления quality_level:**

1. **LLM возвращает:** `overall` (числовая оценка 0-10) и `quality_level` (текстовое значение)
2. **Код валидирует:** Соответствие между `overall` и `quality_level`
3. **При несоответствии:** Используется маппинг на основе `overall`

### Реализация

**В промптах:**
```
"quality_level": "определяется по overall: excellent (>=9), good (>=7), fair (>=5), poor (>=3), not_applicable (<3)"
```

**В коде (reviewer.py):**
```python
if scores.overall >= 9:
    quality_level_expected = "excellent"
elif scores.overall >= 7:
    quality_level_expected = "good"
elif scores.overall >= 5:
    quality_level_expected = "fair"
elif scores.overall >= 3:
    quality_level_expected = "poor"
else:
    quality_level_expected = "not_applicable"
```

**В LangFlow Flow JSON:**
Добавить в промпт:
```
Поле quality_level заполняй по правилу:
- overall >= 9.0 → quality_level: "excellent"
- 7.0 <= overall < 9.0 → quality_level: "good"
- 5.0 <= overall < 7.0 → quality_level: "fair"
- 3.0 <= overall < 5.0 → quality_level: "poor"
- overall < 3.0 или текст не является промптом → quality_level: "not_applicable"
```

---

## История изменений JSON-контракта

### PEl05: Введение JSON-контракта

**Источник:** `n8n/langchain/prompt-review-langchain-code.js`.

- Впервые введён JSON-контракт
- Определена структура `PromptReviewResponse`
- Добавлено ветвление по `is_prompt`

### PEl06: Формализация в Pydantic

**Источник:** `api/app/schemas.py`.

- JSON-контракт формализован в Pydantic-моделях
- Добавлены Enum: `QualityLevel`, `Source`, `ReviewMode`
- Добавлена валидация через Pydantic
- Добавлена автодокументация через FastAPI

### Будущие изменения

- Добавление новых значений в `QualityLevel` — **разрешено**
- Удаление значений из `QualityLevel` — **запрещено**
- Добавление новых полей в `PromptReviewResponse` — **разрешено**
- Удаление полей из `PromptReviewResponse` — **запрещено**

---

## Источники истины

| Компонент | SOT | Назначение |
|-----------|-----|------------|
| Pydantic-модели | `api/app/schemas.py` | Валидация запроса и ответа |
| Промпты | `api/app/pipeline/prompts.py` | Генерация ответа |
| OpenAPI | `/docs`, `/redoc` | HTTP-спецификация |
| Этот документ | `docs/API_CONTRACT.md` | Логический контракт |

---

## Связанные документы

- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура системы
- [SPEC.md](SPEC.md) — продуктовая спецификация
- [README.md](../README.md) — публичное описание проекта