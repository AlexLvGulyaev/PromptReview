# Media Index: Prompt Review Service

---

## 🎯 1. Обзор

Данный каталог систематизирует все медиаматериалы проекта Prompt Review Service для использования в публичной документации GitHub.

**Типы материалов:**
- PNG — скриншоты и изображения
- (В будущем: GIF, SVG, видео)

**Принципы:**
- Медиаматериалы — общие ресурсы проекта, не привязаны к одному документу
- Имена файлов по схеме `{PROJECT}_{VERSION}_{CATEGORY}_{DESCRIPTION}`
- Каждый медиаматериал имеет уникальный идентификатор (IMG-XXX)
- Матрица использования определяет, в каких документах используется каждый медиаматериал

---

## 🖼️ 2. Принцип использования изображений

### Основной принцип

При выборе изображения исходить из вопроса:

**«Какую мысль данного документа необходимо визуально объяснить?»**

Не из вопроса: «Где можно использовать этот скриншот?»

### Алгоритм выбора

1. Определить тезис документа или раздела
2. Определить, что требует визуализации
3. Подобрать изображение, максимально помогающее понять тезис
4. Если подходящего изображения нет — не вставлять

### Правила

- Скриншоты не вставляются только потому, что они существуют
- Каждое изображение должно объяснять конкретную мысль
- Если изображение не помогает пониманию — удалить

### Матрица использования

| Документ | Тезис | Изображения | Обоснование |
|----------|-------|-------------|-------------|
| README.md | Продемонстрировать продукт | IMG-034 (hero), IMG-032, IMG-029 | Web UI и Telegram — главные точки входа |
| USER_GUIDE.md | Научить пользоваться | IMG-030, IMG-031-033, IMG-027-029 | Пошаговые инструкции |
| ARCHITECTURE.md | Объяснить архитектуру | IMG-035 (hero), IMG-003, IMG-010-013, IMG-014-021 | Архитектурные диаграммы |
| API_CONTRACT.md | Показать API | IMG-023-026 | Примеры API-запросов |

---

## 🏷️ 3. Схема нейминга

**Формат:** `{PROJECT}_{VERSION}_{CATEGORY}_{DESCRIPTION}.png`

**Исключение:** портфельные иллюстрации `PR-portfolio-{light,dark}.png` не привязаны к версии продукта — hero-кадры README (LIGHT) и ARCHITECTURE (DARK).

**Версии проекта:**
- `v1` — LangFlow MVP
- `v2` — LangChain
- `v3` — n8n Integration
- `v4` — FastAPI Production (каноническая реализация)

**Категории:**
- `ui` — пользовательские интерфейсы (Web UI, Telegram Bot)
- `api` — API (Swagger, endpoints)
- `arch` — архитектура, схемы
- `flow` — workflow, диаграммы
- `result` — результаты работы (статичные скриншоты)
- `demo` — демонстрационные GIF/видео (зарезервировано)
- `portfolio` — портфельные иллюстрации (витрина AI Portfolio)

---

## 🗂️ 4. Каталог изображений

### v1: LangFlow MVP

| ID | Файл | Категория | Описание |
|----|------|-----------|----------|
| IMG-001 | `PR_v1_ui_langflow_presail.png` | ui | LangFlow интерфейс (Preseil) |
| IMG-002 | `PR_v1_ui_langflow_student.png` | ui | LangFlow интерфейс (Student) |

---

### v2: LangChain

| ID | Файл | Категория | Описание |
|----|------|-----------|----------|
| IMG-003 | `PR_v2_flow_agent_decision.png` | flow | Диаграмма принятия решений агентом |
| IMG-004 | `PR_v2_ui_agentexecutor_main.png` | ui | AgentExecutor главный экран |
| IMG-005 | `PR_v2_ui_agentexecutor_step1.png` | ui | AgentExecutor шаг 1 |
| IMG-006 | `PR_v2_ui_agentexecutor_step2.png` | ui | AgentExecutor шаг 2 |
| IMG-007 | `PR_v2_result_quality.png` | result | Пример ответа (качественный) |
| IMG-008 | `PR_v2_result_detailed.png` | result | Пример ответа (детальный) |
| IMG-009 | `PR_v2_ui_chain_mode.png` | ui | Chain mode интерфейс |
| IMG-010 | `PR_v2_arch_prompt_structure.png` | arch | Структура промпта |
| IMG-011 | `PR_v2_arch_task_dispatcher.png` | arch | Диспетчер задач |
| IMG-012 | `PR_v2_arch_memory.png` | arch | Архитектура памяти |
| IMG-013 | `PR_v2_arch_resources.png` | arch | Ресурсы при вызове |

---

### v3: n8n Integration

| ID | Файл | Категория | Описание |
|----|------|-----------|----------|
| IMG-014 | `PR_v3_flow_langflow_scenario1.png` | flow | Workflow: n8n + LangFlow |
| IMG-015 | `PR_v3_flow_langflow_reuse.png` | flow | Переиспользование Flow v1 |
| IMG-016 | `PR_v3_arch_structured_output.png` | arch | Structured Output Advanced |
| IMG-017 | `PR_v3_arch_prompt_flow.png` | arch | Структура промпта в Flow |
| IMG-018 | `PR_v3_arch_schema.png` | arch | JSON Schema для Structured Output |
| IMG-019 | `PR_v3_flow_langchain_scenario2.png` | flow | Workflow: n8n + LangChain |
| IMG-020 | `PR_v3_result_not_prompt.png` | result | Результат: не промпт |
| IMG-021 | `PR_v3_flow_langflow_full.png` | flow | Полный workflow n8n + LangFlow |
| IMG-022 | `PR_v3_result_langflow_not_prompt.png` | result | LangFlow: не промпт |

---

### v4: FastAPI Production

| ID | Файл | Категория | Описание |
|----|------|-----------|----------|
| IMG-023 | `PR_v4_api_health_check.png` | api | Swagger UI: GET /health |
| IMG-024 | `PR_v4_api_swagger_docs.png` | api | Swagger UI: документация API |
| IMG-025 | `PR_v4_api_review_endpoint.png` | api | Swagger UI: POST /review |
| IMG-026 | `PR_v4_api_response_example.png` | api | Пример ответа API |
| IMG-027 | `PR_v4_ui_telegram_bot.png` | ui | Telegram Bot интерфейс |
| IMG-028 | `PR_v4_result_telegram_not_prompt.png` | result | Telegram: не промпт |
| IMG-029 | `PR_v4_result_telegram_analysis.png` | result | Telegram: анализ промпта |
| IMG-030 | `PR_v4_ui_web_form.png` | ui | Web UI форма |
| IMG-031 | `PR_v4_result_web_not_prompt.png` | result | Web UI: не промпт |
| IMG-032 | `PR_v4_result_web_analysis1.png` | result | Web UI: анализ промпта (1) |
| IMG-033 | `PR_v4_result_web_analysis2.png` | result | Web UI: анализ промпта (2) |

### Портфельные иллюстрации

Сделаны для витрины AI Portfolio; не привязаны к версии продукта.

| ID | Файл | Категория | Описание |
|----|------|-----------|----------|
| IMG-034 | `PR-portfolio-light.png` | portfolio | Витрина кейса LIGHT (продукт глазами пользователя) — hero README |
| IMG-035 | `PR-portfolio-dark.png` | portfolio | Архитектурная витрина DARK (инженерная история под капотом) — hero ARCHITECTURE |

---

## 📊 5. Статистика

### По версиям

| Версия | Изображения | Количество |
|--------|-------------|------------|
| v1 (LangFlow) | IMG-001, IMG-002 | 2 |
| v2 (LangChain) | IMG-003 – IMG-013 | 11 |
| v3 (n8n) | IMG-014 – IMG-022 | 9 |
| v4 (FastAPI) | IMG-023 – IMG-033 | 11 |
| вне версий (портфельные) | IMG-034, IMG-035 | 2 |
| **Всего** | | **35** |

### По категориям

| Категория | Изображения | Количество |
|-----------|-------------|------------|
| **ui** (пользовательские интерфейсы) | IMG-001, IMG-002, IMG-004-006, IMG-009, IMG-027, IMG-030 | 9 |
| **api** (Swagger, endpoints) | IMG-023 – IMG-026 | 4 |
| **arch** (архитектура, схемы) | IMG-010 – IMG-013, IMG-016 – IMG-018 | 6 |
| **flow** (workflow, диаграммы) | IMG-003, IMG-014, IMG-015, IMG-019, IMG-021 | 5 |
| **result** (результаты работы) | IMG-007, IMG-008, IMG-020, IMG-022, IMG-028, IMG-029, IMG-031 – IMG-033 | 9 |
| **portfolio** (портфельные иллюстрации) | IMG-034, IMG-035 | 2 |

---

## 📋 6. Image Usage Matrix

### По документам

| Документ | Изображения | Назначение |
|----------|-------------|------------|
| **README.md** | IMG-034 (hero), IMG-002, IMG-009, IMG-019, IMG-027, IMG-029, IMG-032-033 | Демонстрация эволюции проекта и интерфейсов |
| **USER_GUIDE.md** | IMG-027, IMG-028-033 | Инструкции по использованию Web UI и Telegram |
| **ARCHITECTURE.md** | IMG-035 (hero), IMG-027, IMG-029-030, IMG-032-033 | Демонстрация интерфейсов в разделе User Interfaces |
| **BUSINESS_VALUE.md** | — | Customer-facing слой без технических скриншотов (демонстрация — в SYSTEM_DEMO.md) |
| **SYSTEM_DEMO.md** | IMG-024, IMG-025, IMG-027, IMG-029, IMG-030, IMG-031-033 | Демонстрация продукта: сценарии Web UI, Telegram, API, пограничный случай |
| **langflow/README.md** | IMG-001-002 | Демонстрация LangFlow интерфейсов |
| **langchain/README.md** | IMG-004, IMG-007-009 | Демонстрация LangChain интерфейсов и результатов |
| **n8n/README.md** | IMG-014, IMG-019, IMG-021, IMG-020, IMG-022 | Демонстрация workflow и результатов |

---

### Повторное использование

**Изображения, используемые в нескольких документах:**

| Изображение | Документы | Назначение |
|-------------|-----------|------------|
| IMG-002 (LangFlow интерфейс) | README.md, langflow/README.md | Демонстрация LangFlow MVP |
| IMG-009 (Chain mode) | README.md, langchain/README.md | Демонстрация LangChain |
| IMG-019 (n8n workflow) | README.md, n8n/README.md | Демонстрация n8n интеграции |
| IMG-027 (Telegram Bot) | README.md, ARCHITECTURE.md, USER_GUIDE.md | Демонстрация Telegram Bot |
| IMG-029 (Telegram анализ) | README.md, ARCHITECTURE.md, USER_GUIDE.md | Демонстрация результата анализа |
| IMG-030 (Web UI форма) | ARCHITECTURE.md, USER_GUIDE.md | Демонстрация Web UI |
| IMG-032 (Web UI анализ 1) | README.md, ARCHITECTURE.md, USER_GUIDE.md | Демонстрация результата анализа (часть 1) |
| IMG-033 (Web UI анализ 2) | README.md, ARCHITECTURE.md, USER_GUIDE.md | Демонстрация результата анализа (часть 2) |

---

### Неиспользованные изображения

**Архитектурные схемы (реализованы в Mermaid):**
- IMG-003 — Диаграмма принятия решений агентом (Mermaid в langchain/README.md)
- IMG-010-013 — Архитектурные схемы (Mermaid в ARCHITECTURE.md)
- IMG-015-018 — Архитектурные схемы (Mermaid в ARCHITECTURE.md)

**Специализированные скриншоты:**
- IMG-005-006 — AgentExecutor шаги (не требуются в текущей документации)
- IMG-020 — Результат n8n (не промпт) (использован IMG-022)
- IMG-023-026 — Swagger UI screenshots (API_CONTRACT.md использует JSON примеры вместо скриншотов)
- IMG-033 — Web UI анализ 2 (достаточно IMG-032)

---

### Изображения для демонстрации продукта

**Главная демонстрация (для README):**

| Изображение | Назначение |
|-------------|------------|
| IMG-032 | Web UI: анализ промпта (главный скриншот) |
| IMG-029 | Telegram Bot: анализ промпта |
| IMG-025 | Swagger UI: POST /review (API) |

**Эволюция проекта (для раздела "История"):**

| Версия | Изображение | Назначение |
|------|-------------|------------|
| v1 | IMG-002 | LangFlow MVP |
| v2 | IMG-009 | LangChain Chain mode |
| v3 | IMG-019 | n8n + LangChain |
| v4 | IMG-032 | FastAPI + Web UI |

---

## 🏗️ 7. Архитектурные схемы

### Принцип

Архитектурные схемы реализуются в **Mermaid внутри Markdown**, а не в виде отдельных изображений.

**Обоснование:**
- Mermaid-диаграммы редактируемые
- Версионируются вместе с Markdown
- Не требуют отдельных файлов
- Легко поддерживать

**Файлы с архитектурными схемами:**
- `docs/ARCHITECTURE.md` — основные архитектурные диаграммы

---

## 🗄️ 8. JSON-примеры

JSON-примеры API-запросов и ответов размещены в отдельном каталоге:

**Каталог:** `docs/examples/`

**Файлы:**
- `PR_json_root.json` — GET / пример
- `PR_json_health.json` — GET /health пример
- `PR_json_review_prompt.json` — POST /review (промпт)
- `PR_json_review_not_prompt.json` — POST /review (не промпт)
- `PR_json_error_empty.json` — Ошибка (пустой текст)

**Описание:** [examples/README.md](../examples/README.md)

---


## 📊 9. Статус

✅ Каталог медиаматериалов систематизирован и активно используется в публичной документации.

**Статистика использования:**
- Использовано изображений: 19 из 33 (58%)
- Документов с изображениями: 6 из 8 (75%)
- Повторно используемых: 8 изображений

---

**Статус:** актуален
**Последнее обновление:** 2026-09-16
**История изменений:** [📝 CHANGE_LOG.md](../CHANGE_LOG.md#-1-история-изменений-документации)
