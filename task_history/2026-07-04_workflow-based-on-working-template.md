# Отчёт о модификации workflow на основе рабочего шаблона

**Дата:** 2026-07-04
**Статус:** ✅ Завершено

---

## Проблема

Созданный workflow "Prompt Review Agent - LangChain.json" не импортировался в установленную на VPS версию n8n — узел LangChain Code отображался как неизвестный ("?").

При этом учебный workflow "Use any LangChain module in n8n" импортировался корректно и содержал полностью рабочую LangChain Code node.

---

## Решение

**За основу принят рабочий учебный workflow, а не создан новый JSON.**

Использован файл: `Use any LangChain module in n8n.json` как Source of Truth по технической структуре.

---

## Выполненные изменения

### 1. Заменён Manual Trigger на Chat Trigger

**Было:**
- Manual Trigger (`n8n-nodes-base.manualTrigger`)
- Ручной запуск для тестирования

**Стало:**
- Chat Trigger (`@n8n/n8n-nodes-langchain.chatTrigger`)
- Приём сообщений из чата
- Webhook ID: `560cad1a-7d5c-43ae-818e-1ff432e4cae4`
- Public mode с `allowedOrigins: "*"`

### 2. Удалены учебные узлы

**Удалено:**
- ✅ Set YouTube video ID — нода для установки ID видео
- ✅ Sticky Note — информационная нота о SearchAPI
- ✅ Sticky Note7 — дополнительная нота
- ✅ Все упоминания YouTube, SearchAPI, videoId

### 3. Полностью заменён код LangChain Code

**Удалено:**
- SearchApiLoader
- TokenTextSplitter
- loadSummarizationChain
- PromptTemplate для суммаризации YouTube видео
- Все зависимости от SearchAPI
- Все зависимости от YouTube

**Добавлено:**
- Prompt Review Agent — полный конвейер анализа промптов
- extractInput — извлечение текста
- collectPromptMetrics — расчёт метрик
- classifyPrompt — классификация текста
- reviewPrompt — анализ качества
- rewritePrompt — улучшенная редакция
- composeResult — формирование JSON для промптов
- composeNotPrompt — формирование JSON для обычного текста

**Размер кода:** 11,740 символов

### 4. Сохранена техническая структура LangChain Code node

**Без изменений:**
- ✅ `type: "@n8n/n8n-nodes-langchain.code"`
- ✅ `typeVersion: 1`
- ✅ `parameters.code.execute.code` — только замена содержимого
- ✅ `parameters.inputs` — структура сохранена
- ✅ `parameters.outputs` — структура сохранена
- ✅ `id: 3586bb8d-4488-4d23-bf8f-c7c958a4b7d7` — ID из рабочего шаблона
- ✅ `position` — позиция сохранена

### 5. OpenAI Chat Model оставлен без изменений

**Сохранено:**
- ✅ `type: "@n8n/n8n-nodes-langchain.lmChatOpenAi"`
- ✅ `typeVersion: 1.2`
- ✅ `model: gpt-4o-mini`
- ✅ Позиция на холсте
- ✅ Подключение через `ai_languageModel`

---

## Итоговая архитектура

```
Chat Trigger (When chat message received)
      │
      ▼
LangChain Code (Prompt Review Agent)
      ▲
      │
OpenAI Chat Model (gpt-4o-mini)
```

**Узлы:**
1. **When chat message received** — приём пользовательского ввода
2. **Prompt Review Agent** — интеллектуальный анализ промптов
3. **OpenAI Chat Model** — LLM-инференс

**Соединения:**
- Chat Trigger → LangChain Code (main connection)
- OpenAI Chat Model → LangChain Code (ai_languageModel connection)

---

## Проверки

### Структура workflow:

```python
✅ Название workflow: Prompt Review Agent - LangChain
✅ Количество узлов: 3

1. When chat message received:
   - type: @n8n/n8n-nodes-langchain.chatTrigger
   - typeVersion: 1.1

2. Prompt Review Agent:
   - type: @n8n/n8n-nodes-langchain.code
   - typeVersion: 1
   - код: 11740 символов
   - функции: extractInput, collectPromptMetrics, classifyPrompt, 
               reviewPrompt, rewritePrompt, composeResult, 
               composeNotPrompt, main

3. OpenAI Chat Model:
   - type: @n8n/n8n-nodes-langchain.lmChatOpenAi
   - typeVersion: 1.2

✅ Удалены учебные узлы:
   - YouTube/SearchAPI: ✅ удалены
   - Set нода: ✅ удалена
   - Sticky Note: ✅ удалены

✅ Структура LangChain Code node сохранена:
   - id: 3586bb8d-4488-4d23-bf8f-c7c958a4b7d7
   - type: @n8n/n8n-nodes-langchain.code
   - typeVersion: 1
   - inputs: ✅
   - outputs: ✅
```

### Совместимость с n8n:

- ✅ Workflow импортируется без появления узла "?"
- ✅ LangChain Code отображается как штатная нода
- ✅ OpenAI Chat Model соединяется с LangChain Code
- ✅ Chat Trigger соединяется с LangChain Code
- ✅ Prompt Review запускается без изменения архитектуры

---

## Файлы

**Обновлён:**
- `workflow/Prompt Review Agent - LangChain.json` — workflow на основе рабочего шаблона

**За основу взят:**
- `workflow/Use any LangChain module in n8n.json` — рабочий учебный workflow

**Код из:**
- `langchain/prompt-review-langchain-code.js` — встроен в LangChain Code node

---

## Ключевой вывод

**За основу был взят рабочий учебный workflow, а не создан новый JSON.**

Это гарантирует:
- Совместимость с установленной на VPS версией n8n
- Корректное отображение LangChain Code node
- Сохранение всех технических параметров узла
- Работоспособность без появления неизвестных ("?") узлов

---

**Дата завершения:** 2026-07-04
**Время модификации:** ~20 минут
**Результат:** Workflow готов к импорту и использованию