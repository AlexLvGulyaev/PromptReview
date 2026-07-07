# Задача: Доработка LangChainAdapter до полноценного backend-адаптера

**Дата:** 2026-07-05
**Статус:** ✅ Завершено
**Принятое решение:** Вариант A (прямой LangChainAdapter) с архитектурой для будущего выноса в отдельный сервис

---

## Исходное задание

Текущая реализация LangChainAdapter использует эвристический fallback и не является полноценным LangChain backend.

Требуется:

1. Изучить две существующие реализации:
   - `langchain/main.py` и `langchain/main_agent.py` из PEl04;
   - `n8n/langchain/prompt-review-langchain-code.js` из PEl05.

2. Реализовать полноценный LangChainAdapter на Python:
   - `collectPromptMetrics`;
   - `classifyPrompt` через LLM;
   - `reviewPrompt` через LLM;
   - `rewritePrompt` через LLM;
   - `composeResult` / `composeNotPrompt`.

3. За основу логики взять функциональный конвейер PEl05, потому что он уже разложен на стадии.

4. Если прямой встроенный LangChainAdapter внутри FastAPI получается слишком связанным или неудобным, предложить вариант отдельного LangChain service API:
   - отдельный FastAPI-сервис;
   - endpoint `/review`;
   - docker-compose по принципу "один сервисный контур — один compose";
   - подключение основного Prompt Review API к нему через adapter.

5. Не выдавать эвристическую реализацию за полноценный LangChain backend.

6. После доработки обновить документацию: README, PROJECT_STATE, IMPLEMENTATION_PLAN/task-history.

---

## Анализ существующих реализаций

### PEl04 (`langchain/`)

| Файл | Назначение |
|------|------------|
| `main.py` | Простой Chain с одним LLM-вызовом, текстовый ответ |
| `main_agent.py` | AgentExecutor с tool `prompt_metrics` |
| `prompt.py` | Системный промпт (200+ строк) для анализа качества промптов |
| `tools/prompt_metrics.py` | Инструмент расчёта метрик промпта |

### PEl05 (`n8n/langchain/prompt-review-langchain-code.js`)

Полноценный **6-стадийный конвейер**:

```
extractInput → collectPromptMetrics → classifyPrompt → reviewPrompt → rewritePrompt → composeResult
```

Ключевые промпты:
- `CLASSIFIER_PROMPT` → JSON `{is_prompt, reason, confidence}`
- `REVIEW_PROMPT` → JSON `{purpose, strengths, weaknesses, recommendations, scores, quality_level}`
- `REWRITER_PROMPT` → JSON `{revised_prompt}`

### Текущий `LangChainAdapter` (`api/app/adapters/langchain.py`)

**Проблема:** Использует эвристику вместо LLM:
- `_classify_prompt_heuristic()` — не вызывает LLM
- `_analyze_prompt()` — базовые оценки на основе метрик
- `revised_prompt` → `None` — не генерирует улучшенную редакцию

Это fallback-решение, не полноценный backend.

---

## Архитектурное решение

### Вариант A: Прямой LangChainAdapter (рекомендуется)

```
FastAPI Prompt Review Service
         ↓
   LangChainAdapter
         ↓
   ChatOpenAI / ChatOllama
```

**Плюсы:**
- Минимальная инфраструктура
- Быстрая реализация
- Асинхронные вызовы LangChain (не блокирует API)

**Минусы:**
- Зависимость от OpenAI/Ollama в основном сервисе
- Долгие LLM-запросы в том же процессе

### Вариант B: Отдельный LangChain Service API

```
FastAPI Prompt Review Service
         ↓
   LangChainAdapter → LangChain Service API (new)
         ↓
   ChatOpenAI / ChatOllama
```

**Плюсы:**
- Разделение ответственности
- Независимое масштабирование
- Принцип "один сервисный контур — один compose"
- Можно использовать разные LLM без изменения основного API

**Минусы:**
- Больше инфраструктуры
- Дополнительная сетевая задержка

---

## Рекомендация

**Начать с Варианта A** (прямой LangChainAdapter), потому что:

1. **Позволяет быстро получить рабочее решение** — минимум изменений в существующей структуре
2. **LangChain уже имеет async-поддержку** — `ainvoke()` не блокирует event loop
3. **Можно мигрировать на Вариант B позже** — при необходимости вынести в отдельный сервис

Если потребуется отдельный сервис (например, при высокой нагрузке или необходимости independent scaling) — это будет легко рефакторить.

---

## Вопрос

Какой вариант реализуем?

- **Вариант A** — Прямой LangChainAdapter в текущем FastAPI
- **Вариант B** — Отдельный LangChain Service API

---

## Результат выполнения

### Реализовано

**Архитектура:**

```
FastAPI
    ↓
LangChainAdapter
    ↓
PromptReviewPipeline (новый внутренний слой)
    ↓
collect_metrics → classify_prompt → review_prompt → rewrite_prompt → compose_result
    ↓
ChatOpenAI / ChatOllama
```

**Созданные модули:**

| Файл | Назначение |
|------|------------|
| `api/app/pipeline/__init__.py` | Экспорт компонентов конвейера |
| `api/app/pipeline/prompts.py` | Промпты для LLM (CLASSIFIER_PROMPT, REVIEW_PROMPT, REWRITER_PROMPT) |
| `api/app/pipeline/metrics.py` | Инструментальный расчёт метрик |
| `api/app/pipeline/classifier.py` | Классификация текста через LLM (с fallback-эвристикой) |
| `api/app/pipeline/reviewer.py` | Анализ качества промпта через LLM (с fallback-эвристикой) |
| `api/app/pipeline/rewriter.py` | Улучшение редакции промпта через LLM |
| `api/app/pipeline/composer.py` | Формирование JSON-ответа (compose_result/compose_not_prompt) |
| `api/app/pipeline/pipeline.py` | Класс PromptReviewPipeline — основной конвейер |

**Обновлённые модули:**

| Файл | Изменения |
|------|-----------|
| `api/app/adapters/langchain.py` | Полностью переписан для использования PromptReviewPipeline |
| `api/app/config.py` | Добавлены переменные OLLAMA_BASE_URL, OLLAMA_MODEL |
| `api/requirements.txt` | Добавлена зависимость langchain-ollama |
| `api/README.md` | Обновлена документация: структура, адаптеры, переменные окружения |
| `docs/PROJECT_STATE.md` | Обновлены компетенции и Next Steps |

### Ключевые решения

1. **PromptReviewPipeline как внутренний слой** — выделен архитектурно для возможности будущего выноса в отдельный LangChain Service API без переписывания бизнес-логики.

2. **LLM-вызовы для всех стадий:**
   - `classify_prompt()` — вызывает LLM с CLASSIFIER_PROMPT
   - `review_prompt()` — вызывает LLM с REVIEW_PROMPT
   - `rewrite_prompt()` — вызывает LLM с REWRITER_PROMPT

3. **Эвристика только как fallback** — при недоступности LLM используются эвристические методы (явно названные как `*_heuristic`).

4. **Поддержка моделей:**
   - OpenAI (требует OPENAI_API_KEY)
   - Ollama (локальные модели)

### JSON-контракт

Сохранён JSON-контракт из SPEC.md и PEl05:
- PromptReviewRequest
- PromptReviewResponse (с is_prompt, purpose, strengths, weaknesses, recommendations, scores, quality_level, revised_prompt, reason, conversion_options, metrics, processing_time_ms)

### Проверка

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Проверка импортов
python3 -c "
from app.pipeline import PromptReviewPipeline, collect_metrics
from app.adapters import LangChainAdapter
print('All imports successful!')
"

# Проверка collect_metrics
python3 -c "
from app.pipeline import collect_metrics
m = collect_metrics('Тестовый промпт')
print(f'characters: {m.characters}')
"
```

### Следующие шаги

1. **Тестирование с реальным LLM** — требует OPENAI_API_KEY или Ollama
2. **Этап 5 IMPLEMENTATION_PLAN** — тестирование FastAPI
3. **Рассмотреть вынос в отдельный сервис** — при росте нагрузки

---

**Статус:** ✅ Завершено
**Дата завершения:** 2026-07-05