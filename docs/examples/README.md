# API Examples

**Last Updated:** 2026-07-07
**Project:** Prompt Review Service
**Status:**
 Каталог примеров API-запросов и ответов

---

## Обзор

Данный каталог содержит примеры API-запросов и ответов для Prompt Review Service.

**Типы файлов:**
- JSON — примеры запросов и ответов API
- (В будущем: curl, Python, JavaScript)

---

## Примеры

### JSON-001: GET /

**Файл:** `PEL06_json_root.json`

**Endpoint:** `GET /`

**Описание:** Корневой endpoint, возвращает информацию о сервисе.

**Пример ответа:**
```json
{"message": "Prompt Review API"}
```

---

### JSON-002: GET /health

**Файл:** `PEL06_json_health.json`

**Endpoint:** `GET /health`

**Описание:** Health check endpoint, возвращает статус сервиса.

**Пример ответа:**
```json
{"status": "healthy"}
```

---

### JSON-003: POST /review (промпт)

**Файл:** `PEL06_json_review_prompt.json`

**Endpoint:** `POST /review`

**Описание:** Анализ промпта — текст является промптом для LLM.

**Ключевые поля ответа:**
- `is_prompt: true` — текст классифицирован как промпт
- `purpose` — определённое назначение промпта
- `strengths` — сильные стороны
- `weaknesses` — слабые стороны
- `recommendations` — рекомендации по улучшению
- `scores` — оценки по критериям
- `revised_prompt` — улучшенная редакция

---

### JSON-004: POST /review (не промпт)

**Файл:** `PEL06_json_review_not_prompt.json`

**Endpoint:** `POST /review`

**Описание:** Анализ текста — текст не является промптом для LLM.

**Ключевые поля ответа:**
- `is_prompt: false` — текст классифицирован как не промпт
- `purpose` — интерпретация текста

---

### JSON-005: Ошибка (пустой текст)

**Файл:** `PEL06_json_error_empty.json`

**Endpoint:** `POST /review`

**Описание:** Пример ошибки при пустом тексте.

**Пример ответа:**
```json
{
  "detail": "prompt_text cannot be empty"
}
```

---

## Использование в документации

| Документ | Примеры | Назначение |
|----------|---------|------------|
| API_CONTRACT.md | Все | Полный контракт API |
| README.md | JSON-003 | Пример запроса |
| USER_GUIDE.md | JSON-002, JSON-003 | Инструкции по использованию |

---

## Расширение

При добавлении новых примеров:

1. Использовать схему именования: `PEL06_json_{description}.json`
2. Описать пример в данном README
3. Добавить ссылку в API_CONTRACT.md

---

## История изменений

**2026-07-07:**
- ✅ Создан каталог `docs/examples/`
- ✅ Перемещены JSON-файлы из `docs/screenshots/`
- ✅ Создан README.md с описанием примеров