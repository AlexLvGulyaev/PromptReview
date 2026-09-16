# API Examples

---

## 🎯 1. Обзор

Данный каталог содержит примеры API-запросов и ответов для Prompt Review Service.

**Типы файлов:**
- JSON — примеры запросов и ответов API
- (В будущем: curl, Python, JavaScript)

---

## ⚙️ 2. CI/CD интеграция

Пример проверки качества промпта в GitLab CI:

```yaml
# Анализ промпта при каждом коммите
analyze_prompt:
  script:
    - |
      curl -X POST http://prompt-review:8000/review \
        -H "Content-Type: application/json" \
        -d @prompt.json | jq '.scores.clarity'
```

Сценарий: промпты хранятся отдельными файлами в репозитории, пайплайн отправляет их в `/review` и проверяет оценки по критериям (`scores`). Поле `scores` описано в [API_CONTRACT.md](../API_CONTRACT.md).

---

## 📋 3. Примеры

### JSON-001: GET /

**Файл:** `PR_json_root.json`

**Endpoint:** `GET /`

**Описание:** Корневой endpoint, возвращает информацию о сервисе.

**Пример ответа:**
```json
{"message": "Prompt Review API"}
```

---

### JSON-002: GET /health

**Файл:** `PR_json_health.json`

**Endpoint:** `GET /health`

**Описание:** Health check endpoint, возвращает статус сервиса.

**Пример ответа:**
```json
{"status": "healthy"}
```

---

### JSON-003: POST /review (промпт)

**Файл:** `PR_json_review_prompt.json`

**Endpoint:** `POST /review`

**Описание:** Анализ промпта — текст является промптом для LLM.

**Поля ответа:**
- `is_prompt: true` — текст классифицирован как промпт
- `purpose` — определённое назначение промпта
- `strengths` — сильные стороны
- `weaknesses` — слабые стороны
- `recommendations` — рекомендации по улучшению
- `scores` — оценки по критериям
- `revised_prompt` — улучшенная редакция

---

### JSON-004: POST /review (не промпт)

**Файл:** `PR_json_review_not_prompt.json`

**Endpoint:** `POST /review`

**Описание:** Анализ текста — текст не является промптом для LLM.

**Поля ответа:**
- `is_prompt: false` — текст классифицирован как не промпт
- `purpose` — интерпретация текста

---

### JSON-005: Ошибка (пустой текст)

**Файл:** `PR_json_error_empty.json`

**Endpoint:** `POST /review`

**Описание:** Пример ошибки при пустом тексте.

**Пример ответа:**
```json
{
  "detail": "prompt_text cannot be empty"
}
```

---

## 📄 4. Использование в документации

| Документ | Примеры | Назначение |
|----------|---------|------------|
| API_CONTRACT.md | Все | Полный контракт API |
| README.md | JSON-003 | Пример запроса |
| USER_GUIDE.md | JSON-002, JSON-003 | Инструкции по использованию |

---

## 🚀 5. Расширение

При добавлении новых примеров:

1. Использовать схему именования: `PR_json_{description}.json`
2. Описать пример в данном README
3. Добавить ссылку в API_CONTRACT.md

---

---

**Статус:** актуален
**Последнее обновление:** 2026-09-16
**История изменений:** [📝 CHANGE_LOG.md](../CHANGE_LOG.md#-1-история-изменений-документации)
