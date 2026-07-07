# Task: Исследование Format Instructions в Langflow

**Дата:** 2026-07-04
**Статус:** Завершено

---

## Исходное задание

> В документации langflow я читаю вот это:
> [описание Structured Output компонента с Format Instructions]
> В интерфейсе LF я НЕ ВИЖУ возможности редактирования Format Instructions. Клод, нужно перерыть документацию и найти, где именно в UI редактируется эта информация.

---

## Установленная версия Langflow

**Версия:** `langflowai/langflow:1.10.1` (latest stable, 23 июня 2025)

**Источник:** `task-history/2026-07-04_langflow-version-research.md`

**Причина выбора:**
1. MissingGreenlet фикс (PR #6258) — содержится в версиях 1.2.0+ ✅
2. Security fixes — критические исправления безопасности в 1.9.3+ ✅
3. Pinned version — предсказуемые обновления, возможность отката ✅

---

## Причина отсутствия Format Instructions в UI

### Баг #13595 — Hidden fields not accessible in Inspection Panel

**GitHub Issue:** [#13595](https://github.com/langflow-ai/langflow/issues/13595)

**Проблема:**
Поля с `advanced=True` были скрыты **везде** — не только в основном UI компонента, но и в **Inspection Panel**.

**Причина:**
Frontend использовал `HIDDEN_FIELDS` allow-list, который блокировал отображение advanced-полей даже в панели инспекции.

**Результат:**
Поле Format Instructions (`system_prompt`) **полностью недоступно** в UI — нигде нельзя отредактировать.

**Статус:**
- Баг исправлен в **PR #13626**
- Включён в версию **1.11.0**

---

## Ситуация с версиями

| Версия | Статус | Дата | Format Instructions доступен? |
|--------|--------|------|------------------------------|
| **1.10.1** (ваша) | ✅ Latest stable | 23 июня 2025 | ❌ Нет (баг #13595) |
| **1.11.0** | ⚠️ Development build (dev30) | Pre-release | ✅ Да (исправлено) |
| **1.11.0 stable** | ❌ Не выпущена | — | — |

**Критично:** Версии 1.11.0 как стабильного релиза **не существует**. Есть только dev-build на PyPI, не production-ready.

---

## Почему обновление невозможно

1. **1.10.1 — последняя стабильная версия**
2. **1.11.0 — development build**, не подходит для production
3. **Обновляться некуда** — stable 1.11.0 ещё не выпущена

---

## Решение: обходной путь через JSON

Поскольку обновление до 1.11.0 stable невозможно, используйте JSON-редактирование:

### Шаги

1. **Экспортировать flow в JSON**
   - В Langflow UI: меню flow → Export

2. **Найти поле `system_prompt` в JSON**
   ```json
   {
     "data": {
       "node": {
         "data": {
           "node": {
             "template": {
               "system_prompt": {
                 "type": "str",
                 "required": true,
                 "placeholder": "",
                 "show": true,
                 "name": "system_prompt",
                 "display_name": "Format Instructions",
                 "advanced": true,  // ← изменить на false
                 "value": "..."
               }
             }
           }
         }
       }
     }
   }
   ```

3. **Изменить `"advanced": true` → `"advanced": false`**

4. **Импортировать flow обратно**
   - В Langflow UI: New Flow → Import

5. **Результат:** Поле Format Instructions появится в основном UI компонента

---

## Импорт/экспорт Flow в Langflow 1.10.1

### Экспорт Flow

**Способ 1: Projects Page**
1. Открыть **Projects page** (главная страница)
2. Найти flow
3. Нажать **⋮ (More)** → **Export**

**Способ 2: Из редактора Flow**
1. Открыть flow
2. Нажать **Share** → **Export**

**Способ 3: API**
```python
import requests

LANGFLOW_URL = "https://langflow.alex-n8n.site"
API_KEY = "your-api-key"

response = requests.post(
    f"{LANGFLOW_URL}/api/v1/flows/download/",
    headers={"x-api-key": API_KEY},
    json=[flow_id]
)
with open("flow.json", "wb") as f:
    f.write(response.content)
```

### Импорт Flow

**Способ 1: Projects Page**
1. Открыть **Projects page**
2. Нажать **"Upload a flow"** или **"Upload Folder"**
3. Выбрать JSON файл

**Способ 2: Drag & Drop**
Перетащить JSON файл в любое место интерфейса Langflow.

**Способ 3: API**
```python
import requests

LANGFLOW_URL = "https://langflow.alex-n8n.site"
API_KEY = "your-api-key"

files = {"file": open("flow.json", "rb")}
response = requests.post(
    f"{LANGFLOW_URL}/api/v1/flows/upload/",
    headers={"x-api-key": API_KEY},
    files=files
)
print(response.json())
```

### Если кнопка Import отсутствует в UI

1. **Проверить расположение** — кнопка находится на **Projects page**, не внутри flow
2. **Название кнопки** — может называться **"Upload Folder"** (переименовано в PR #2125)
3. **Использовать Drag & Drop** — работает на любой странице
4. **Использовать API** — endpoint `/api/v1/flows/upload/`

---

## Характеристики поля Format Instructions

| Параметр | Значение |
|----------|----------|
| **Display Name** | Format Instructions |
| **Внутреннее имя** | `system_prompt` |
| **Тип ввода** | MultilineInput (многострочное текстовое поле) |
| **Категория** | Advanced (расширенные настройки) |
| **Обязательное** | Да |

### Default Value

```
You are an AI that extracts structured JSON objects from unstructured text.
Use a predefined schema with expected types (str, int, float, bool, dict).
Extract ALL relevant instances that match the schema - if multiple patterns exist, capture them all.
Fill missing or ambiguous values with defaults: null for missing values.
Remove exact duplicates.
Always return valid JSON.
```

### Для чего используется

Поле содержит инструкции для LLM:
- какие данные извлечь из исходного материала
- как отформатировать результат
- как обрабатывать исключения
- как работать с пропущенными значениями

---

## Другие параметры компонента Structured Output

| Display Name | Type | Required | Advanced |
|--------------|------|----------|----------|
| Language Model | ModelInput | Yes | No |
| API Key | SecretStrInput | No | Yes |
| Input Message | MultilineInput | Yes | No |
| Schema Name | MessageTextInput | No | Yes |
| Output Schema | TableInput | Yes | No |

---

## Источники

- [GitHub Issue #13595 — Missing input data in inspector panel](https://github.com/langflow-ai/langflow/issues/13595)
- [GitHub PR #13626 — Fix hidden fields](https://github.com/langflow-ai/langflow/pull/13626)
- [GitHub Releases — Langflow](https://github.com/langflow-ai/langflow/releases)
- [v1.10.1 Release](https://github.com/langflow-ai/langflow/releases/tag/v1.10.1)
- [PyPI langflow 1.11.0.dev30](https://pypi.org/project/langflow/1.11.0.dev30/)
- [Structured Output | Langflow Documentation](https://docs.langflow.org/structured-output)
- [structured_output.py source code](https://raw.githubusercontent.com/langflow-ai/langflow/refs/heads/main/src/lfx/src/lfx/components/llm_operations/structured_output.py)
- [Import and export flows | Langflow Documentation](https://docs.langflow.org/concepts-flows-import)
- [Flow management endpoints | Langflow Documentation](https://docs.langflow.org/api-flows)
- [GitHub Issue #4070 — Import feature broken](https://github.com/langflow-ai/langflow/issues/4070)
- [GitHub PR #2125 — Rename upload button to Upload Folder](https://github.com/langflow-ai/langflow/pull/2125)

---

## Выводы

1. **Поле Format Instructions отсутствует из-за бага #13595** — исправлено в 1.11.0, но эта версия не выпущена как stable
2. **Версия 1.10.1 — правильный выбор для production** — обновляться некуда
3. **Обходной путь** — экспорт JSON, изменение `advanced: false`, импорт
4. **Следить за релизом 1.11.0 stable** — после выхода можно обновиться