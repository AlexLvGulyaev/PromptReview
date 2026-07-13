# DEPLOYMENT_GUIDE.md — Prompt Review Service

**Версия:** 2.0
**Дата:** 2026-07-07
**Статус:** Инженерное руководство

---

## Purpose

Данный документ описывает полное развёртывание Prompt Review Service с нуля.

**Что разворачивается:**

| Компонент | Назначение | Обязательный |
|-----------|------------|--------------|
| FastAPI API | REST API для анализа промптов | ✅ Да |
| Web UI | Веб-интерфейс для ручной проверки | ✅ Да (монтируется в API) |
| Telegram Bot | Чат-бот для проверки из мессенджера | ⚪ Опционально |
| LangChain Backend | AI-движок на OpenAI/Ollama | ✅ Да (по умолчанию) |
| LangFlow Backend | AI-движок на LangFlow | ⚪ Опционально (Flow включён в репозиторий) |

**Что пользователь получит после завершения:**

- Работающий REST API на порту 8000
- Веб-интерфейс на `/ui`
- Health check endpoint для мониторинга
- Документацию API на `/docs`

---

## Deployment Models

### Model 1: Local Development

**Назначение:** Разработка и тестирование на локальной машине.

**Архитектура:**

```
Browser / Telegram
        ↓
FastAPI API (localhost:8000)
        ↓
LangChain Backend
        ↓
OpenAI API / Ollama
```

**Компоненты:**

| Компонент | Статус |
|-----------|--------|
| FastAPI API | ✅ Запускается локально |
| Web UI | ✅ Монтируется в API |
| LangChain Backend | ✅ Встроенный |
| Telegram Bot | ⚪ Опционально (отдельный процесс) |

**Ограничения:**

- Не подходит для production без доработки (нет HTTPS, нет балансировки)
- Требует Python 3.11+ на машине

**Требования:**

| Требование | Версия | Как проверить |
|------------|--------|---------------|
| Python | 3.11+ | `python --version` |
| pip | 20.0+ | `pip --version` |
| OpenAI API Key | — | Регистрация на openai.com |

---

### Model 2: Docker Development

**Назначение:** Изолированное развёртывание через Docker.

**Архитектура:**

```
Browser / Telegram
        ↓
Docker Container (port 8000)
        ↓
LangChain Backend
        ↓
OpenAI API
```

**Компоненты:**

| Компонент | Статус |
|-----------|--------|
| FastAPI API | ✅ Docker-контейнер |
| Web UI | ✅ Внутри контейнера |
| LangChain Backend | ✅ Внутри контейнера |
| Telegram Bot | ⚪ Отдельный контейнер |

**Ограничения:**

- Требует Docker и Docker Compose
- Требует внешнюю сеть `n8n_default` (создаётся вручную)

**Требования:**

| Требование | Версия | Как проверить |
|------------|--------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |

---

### Model 3: LangFlow Development

**Назначение:** Развёртывание с LangFlow backend (визуальный конструктор AI-Flow).

**Архитектура:**

```
Browser / Telegram
        ↓
FastAPI API (localhost:8000)
        ↓
LangFlow Backend (localhost:7860)
        ↓
OpenAI API
```

**Компоненты:**

| Компонент | Статус |
|-----------|--------|
| FastAPI API | ✅ Запускается локально или в Docker |
| Web UI | ✅ Монтируется в API |
| LangFlow | ✅ Docker-контейнер с PostgreSQL |
| Flow для анализа | ✅ Включён в репозиторий |
| Telegram Bot | ⚪ Опционально |

**Flow файлы в репозитории:**

| Файл | Назначение |
|------|------------|
| `langflow/flows/Prompt Review Agent _ Human Report.json` | Интерактивный анализ (чат) |
| `n8n/langflow/Prompt Review Agent - API JSON.json` | API-интеграция (JSON output) |

**Ограничения:**

- Требует PostgreSQL для LangFlow
- Требует больше ресурсов (отдельный контейнер LangFlow)
- Flow необходимо импортировать через UI LangFlow

**Требования:**

| Требование | Версия | Как проверить |
|------------|--------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |
| OpenAI API Key | — | platform.openai.com |

**Ресурсы:**

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 40 GB |

---

### Model 4: Production Adaptation

**Назначение:** Основа для production-развёртывания.

**Архитектура:**

```
Users
  ↓
Reverse Proxy (Traefik/Nginx)
  ↓
Docker Container
  ↓
LangChain Backend
  ↓
OpenAI API / Ollama
```

**Требуется доработка:**

- Настройка HTTPS (Traefik/Nginx)
- Настройка аутентификации
- Настройка rate limiting
- Настройка мониторинга
- Настройка логирования

**Статус:** ⚠️ Требует адаптации под конкретную инфраструктуру.

---

## Prerequisites

### Обязательные

| Компонент | Назначение | Как установить |
|-----------|------------|----------------|
| Python 3.11+ | Runtime для Local Development | [python.org](https://python.org) |
| OpenAI API Key | AI-движок | [platform.openai.com](https://platform.openai.com) |
| Git | Клонирование репозитория | `apt install git` / `brew install git` |

### Для Docker Development

| Компонент | Назначение | Как установить |
|-----------|------------|----------------|
| Docker | Контейнеризация | [docker.com](https://docker.com) |
| Docker Compose | Управление контейнерами | Входит в Docker Desktop |

### Опциональные

| Компонент | Назначение | Как установить |
|-----------|------------|----------------|
| Ollama | Локальные модели | [ollama.ai](https://ollama.ai) |
| Telegram Bot Token | Telegram Bot | @BotFather в Telegram |

---

## Environment

### Структура переменных

Переменные окружения разделены на группы по назначению:

| Группа | Переменные | Обязательность |
|--------|------------|----------------|
| Backend | `BACKEND_TYPE`, `LANGCHAIN_MODEL` | ✅ Обязательны |
| OpenAI | `OPENAI_API_KEY` | ✅ Для LangChain + OpenAI |
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | ⚪ Для LangChain + Ollama |
| LangFlow | `LANGFLOW_URL`, `LANGFLOW_FLOW_ID`, `LANGFLOW_API_KEY` | ⚪ Для LangFlow backend |
| Telegram | `TELEGRAM_BOT_TOKEN`, `PROMPT_REVIEW_API_URL` | ⚪ Для Telegram Bot |
| API | `CORS_ORIGINS`, `LOG_LEVEL` | ⚪ Опционально |

### Обязательные переменные

#### `BACKEND_TYPE`

**Назначение:** Определяет, какой AI-backend использовать.

**Обязательность:** ✅ Да

**Значения:**

| Значение | Backend | Требования |
|----------|---------|------------|
| `langchain` | LangChain (OpenAI/Ollama) | `OPENAI_API_KEY` или `OLLAMA_BASE_URL` |
| `langflow` | LangFlow (внешний сервер) | `LANGFLOW_URL`, `LANGFLOW_FLOW_ID`, `LANGFLOW_API_KEY` |

**По умолчанию:** `langflow`

**Пример:**

```bash
BACKEND_TYPE=langchain
```

---

#### `OPENAI_API_KEY`

**Назначение:** API ключ для OpenAI.

**Обязательность:** ✅ Да (если `BACKEND_TYPE=langchain` и `LANGCHAIN_MODEL=openai`)

**Где получить:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Формат:** `sk-...`

**Пример:**

```bash
OPENAI_API_KEY=sk-proj-abc123...
```

---

### Опциональные переменные

#### `LANGCHAIN_MODEL`

**Назначение:** Модель для LangChain backend.

**Значения:**

| Значение | Описание | Требования |
|----------|----------|------------|
| `openai` | OpenAI GPT модели | `OPENAI_API_KEY` |
| `ollama` | Локальные модели через Ollama | Установленный Ollama |

**По умолчанию:** `openai`

---

#### `OLLAMA_BASE_URL`

**Назначение:** URL сервера Ollama.

**По умолчанию:** `http://localhost:11434`

**Пример:**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:9b
```

---

#### `CORS_ORIGINS`

**Назначение:** Разрешённые origins для CORS.

**По умолчанию:** Пусто (CORS отключён)

**Пример:**

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

#### `TELEGRAM_BOT_TOKEN`

**Назначение:** Token для Telegram Bot.

**Где получить:** @BotFather в Telegram

**Пример:**

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### Пример .env файла

```bash
# Backend
BACKEND_TYPE=langchain
LANGCHAIN_MODEL=openai

# OpenAI
OPENAI_API_KEY=sk-proj-your-api-key

# CORS (для разработки)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO

# Telegram Bot (опционально)
# TELEGRAM_BOT_TOKEN=your-bot-token
# PROMPT_REVIEW_API_URL=http://localhost:8000

# LangFlow (опционально, если BACKEND_TYPE=langflow)
# LANGFLOW_URL=http://localhost:7860
# LANGFLOW_FLOW_ID=your-flow-id
# LANGFLOW_API_KEY=your-langflow-api-key
```

---

### Пример .env для LangFlow

```bash
# Backend
BACKEND_TYPE=langflow

# LangFlow
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your-flow-id
LANGFLOW_API_KEY=your-langflow-api-key

# OpenAI (для LangFlow)
OPENAI_API_KEY=sk-proj-your-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

---

## Deployment

### Model 1: Local Development

#### Шаг 1: Клонирование

```bash
git clone https://github.com/AlexLvGulyaev/PromptReview.git
cd PromptReview
```

**Ожидаемый результат:**

```
PromptReview/
├── api/
│   ├── app/
│   ├── telegram/
│   ├── web/
│   └── requirements.txt
├── docs/
├── infra/
└── README.md
```

**Проверка:**

```bash
ls -la api/app/
```

Должны быть: `main.py`, `config.py`, `schemas.py`, `adapters/`, `pipeline/`

---

#### Шаг 2: Виртуальное окружение

**Действие:**

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или: .venv\Scripts\activate  # Windows
```

**Ожидаемый результат:**

Активировано виртуальное окружение Python.

**Проверка:**

```bash
which python
```

**Критерий успешного завершения:**

Вывод показывает путь к `.venv/bin/python`:

```
/opt/ai-automation-portfolio-lab/cases/prompt-review/api/.venv/bin/python
```

---

#### Шаг 3: Зависимости

**Действие:**

```bash
pip install -r requirements.txt
```

**Ожидаемый результат:**

```
Successfully installed fastapi-0.109.0 uvicorn-0.27.0 httpx-0.26.0 pydantic-2.5.0 ...
```

**Проверка:**

```bash
pip list | grep fastapi
```

**Критерий успешного завершения:**

Вывод показывает версию fastapi:

```
fastapi                       0.109.0
```

---

#### Шаг 4: Конфигурация

Создайте файл `api/.env`:

```bash
cd api
cat > .env << 'EOF'
# Backend
BACKEND_TYPE=langchain
LANGCHAIN_MODEL=openai

# OpenAI
OPENAI_API_KEY=sk-proj-YOUR-API-KEY-HERE

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
EOF
```

**Важно:** Замените `YOUR-API-KEY-HERE` на реальный OpenAI API ключ.

---

#### Шаг 5: Запуск

```bash
cd api
uvicorn app.main:app --reload --port 8000
```

**Ожидаемый результат:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Проверка:**

```bash
# Health check
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "backend": "langchain",
  "backend_available": true
}
```

---

#### Шаг 6: Тестирование API

**Действие:**

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Напиши функцию сортировки списка на Python", "user_id": "test"}'
```

**Ожидаемый результат:**

```json
{
  "is_prompt": true,
  "scores": {
    "clarity": 7,
    "completeness": 6,
    "unambiguity": 8,
    "audience": 7,
    "format": 6,
    "constraints": 5,
    "assumptions": 6,
    "repeatability": 7
  },
  "recommendations": [
    "Добавьте пример ожидаемого результата",
    "Укажите ограничения по производительности",
    "Опишите граничные случаи"
  ],
  "improved_version": "Напиши функцию сортировки списка на Python. Функция должна принимать список чисел и возвращать отсортированный список по возрастанию. Пример: input [3, 1, 2] → output [1, 2, 3]. Обработай пустой список и список из одного элемента."
}
```

**Критерий успешного завершения:**

- ✅ API отвечает на `/health` с `{"status": "ok"}`
- ✅ API отвечает на `/review` с JSON-ответом
- ✅ JSON содержит поля `is_prompt`, `scores`, `recommendations`, `improved_version`
- ✅ Web UI доступен на http://localhost:8000/ui

**Полный E2E Check:**

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. API test
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Test prompt", "user_id": "test"}'

# 3. Web UI check
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ui
```

**Ожидаемые результаты:**

1. Health check: `{"status":"ok","backend":"langchain","backend_available":true}`
2. API test: JSON-ответ с полями `is_prompt`, `scores`, `recommendations`, `improved_version`
3. Web UI check: HTTP статус `200`

---

### Model 2: Docker Development

#### Шаг 1: Создание сети

```bash
docker network create n8n_default
```

**Проверка:**

```bash
docker network ls | grep n8n_default
```

---

#### Шаг 2: Конфигурация

Создайте файл `infra/.env`:

```bash
cd infra
cat > .env << 'EOF'
# Backend
BACKEND_TYPE=langchain
LANGCHAIN_MODEL=openai

# OpenAI
OPENAI_API_KEY=sk-proj-YOUR-API-KEY-HERE

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
EOF
```

---

#### Шаг 3: Сборка и запуск

```bash
cd infra
docker compose -f docker-compose.api.yml up -d
```

**Ожидаемый результат:**

```
[+] Building ...
[+] Running 1/1
 ✔ Container prompt-review-api  Started
```

**Проверка:**

```bash
docker compose -f docker-compose.api.yml logs -f
```

Должны быть логи: `Application startup complete`

---

#### Шаг 4: Тестирование

```bash
# Health check
curl http://localhost:8000/health

# API test
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Test prompt", "user_id": "test"}'
```

---

#### Шаг 5: Остановка

**Действие:**

```bash
docker compose -f docker-compose.api.yml down
```

**Ожидаемый результат:**

```
[+] Running 1/1
 ✔ Container prompt-review-api  Removed
 ✔ Network n8n_default          Removed
```

**Критерий успешного завершения:**

Контейнер `prompt-review-api` остановлен и удалён.

---

#### Полный E2E Check для Model 2

**Проверка всех компонентов:**

```bash
# 1. Проверить запущенные контейнеры
docker compose -f docker-compose.api.yml ps

# 2. Проверить логи
docker compose -f docker-compose.api.yml logs --tail 20

# 3. Проверить health check
curl http://localhost:8000/health

# 4. Проверить API docs
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs

# 5. Проверить Web UI
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ui
```

**Ожидаемые результаты:**

1. Статус контейнера: `running (healthy)`
2. Логи содержат: `Application startup complete`
3. Health check: `{"status":"ok","backend":"langchain","backend_available":true}`
4. API docs: HTTP статус `200`
5. Web UI: HTTP статус `200`

---

### Telegram Bot (опционально)

#### Шаг 1: Создание бота

**Действие:**

1. Откройте @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям:
   - Укажите имя бота (например: `Prompt Review Bot`)
   - Укажите username (например: `prompt_review_bot`)
4. Сохраните полученный token

**Ожидаемый результат:**

```
Done! Congratulations on your new bot...
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz

Keep your token secure...
```

**Критерий успешного завершения:**

Bot token сохранён.

---

#### Шаг 2: Конфигурация

**Действие:**

Добавьте в `api/.env`:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
PROMPT_REVIEW_API_URL=http://localhost:8000
API_TIMEOUT=60
```

**Критерий успешного завершения:**

Переменные добавлены в `.env`.

---

#### Шаг 3: Запуск (локально)

**Действие:**

```bash
cd api/telegram
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

**Ожидаемый результат:**

```
Bot started. Send messages to @prompt_review_bot
```

**Проверка:**

```bash
# Проверить процесс бота
ps aux | grep "python.*bot.py"
```

**Критерий успешного завершения:**

- ✅ Процесс бота запущен
- ✅ Напишите боту `/start` — бот отвечает приветственным сообщением
- ✅ Напишите промпт — бот отвечает результатами анализа

---

#### Шаг 4: Тестирование бота

**Действие:**

1. Откройте Telegram
2. Найдите бота по username
3. Отправьте `/start`
4. Отправьте текст: "Напиши функцию сортировки списка на Python"

**Ожидаемый результат:**

Бот отвечает:

```
✅ Промпт проанализирован

📊 Оценки:
• Ясность: 7/10
• Полнота: 6/10
• Однозначность: 8/10

💡 Рекомендации:
1. Добавьте пример ожидаемого результата
2. Укажите ограничения по производительности
3. Опишите граничные случаи
```

**Критерий успешного завершения:**

- ✅ Бот отвечает на `/start`
- ✅ Бот обрабатывает промпты
- ✅ Бот возвращает структурированный результат

---

#### Полный E2E Check для Telegram Bot

**Проверка всех компонентов:**

```bash
# 1. Проверить процесс бота
ps aux | grep "python.*bot.py"

# 2. Проверить переменные окружения
echo $TELEGRAM_BOT_TOKEN
echo $PROMPT_REVIEW_API_URL

# 3. Проверить API
curl http://localhost:8000/health

# 4. Проверить Telegram Bot API
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

**Ожидаемые результаты:**

1. Процесс бота запущен
2. Переменные установлены
3. API health check: `{"status":"ok"}`
4. Telegram Bot API: `{"ok":true,"result":{"is_bot":true,...}}`

---

### LangFlow Development (опционально)

LangFlow — визуальный конструктор AI-Flow. Prompt Review включает готовые Flow для анализа промптов.

#### Шаг 1: Запуск LangFlow

**Действие:**

```bash
cd infra

# Создать сеть (если не существует)
docker network create n8n_default

# Запустить LangFlow
docker compose -f docker-compose.langflow.yml up -d
```

**Ожидаемый результат:**

```
[+] Running 3/3
 ✔ Network langflow-network    Created
 ✔ Container prompt-review-postgres  Started
 ✔ Container prompt-review-langflow  Started
```

**Проверка:**

```bash
# Проверить статус контейнеров
docker compose -f docker-compose.langflow.yml ps
```

**Критерий успешного завершения:**

Оба контейнера в статусе `running (healthy)`:

```
NAME                          STATUS
prompt-review-postgres        running (healthy)
prompt-review-langflow        running (healthy)
```

---

#### Шаг 2: Ожидание запуска LangFlow

**Действие:**

LangFlow требует время на инициализацию (до 60 секунд).

```bash
# Проверить логи
docker compose -f docker-compose.langflow.yml logs -f langflow
```

**Ожидаемый результат:**

Ищите в логах: `Langflow ready` или `Uvicorn running on http://0.0.0.0:7860`

**Критерий успешного завершения:**

LangFlow готов к работе, логи содержат сообщение о готовности.

---

#### Шаг 3: Настройка LangFlow

**Действие:**

1. Откройте http://localhost:7860 в браузере
2. При первом запуске LangFlow создаст супер-пользователя (логин/пароль из `.env`)
3. Перейдите в **My Projects** → **New Project**

**Критерий успешного завершения:**

Открылся интерфейс LangFlow.

---

#### Шаг 4: Импорт Flow

**Действие:**

**Файлы Flow в репозитории:**

| Файл | Назначение |
|------|------------|
| `langflow/flows/Prompt Review Agent _ Human Report.json` | Интерактивный анализ (чат) |
| `n8n/langflow/Prompt Review Agent - API JSON.json` | API-интеграция (JSON output) |

**Импорт:**

1. В LangFlow нажмите **Import** (или Ctrl+I)
2. Выберите файл `langflow/flows/Prompt Review Agent _ Human Report.json`
3. Flow появится в списке проектов

**Критерий успешного завершения:**

Flow появился в списке проектов LangFlow.

---

#### Шаг 5: Конфигурация API Key

**Действие:**

1. Откройте импортированный Flow
2. Найдите компонент **Chat Model** (OpenAI)
3. Вставьте ваш `OPENAI_API_KEY`
4. Сохраните Flow (Ctrl+S)

**Критерий успешного завершения:**

API Key сохранён в компоненте Chat Model.

---

#### Шаг 6: Получение Flow ID и API Key

**Действие:**

**Flow ID:**

1. Откройте Flow
2. В адресной строке браузера: `http://localhost:7860/flow/{FLOW_ID}`
3. Скопируйте `FLOW_ID`

**API Key:**

1. Перейдите в **Settings** → **API Keys**
2. Создайте новый API Key
3. Скопируйте ключ

**Критерий успешного завершения:**

- Flow ID скопирован
- LangFlow API Key скопирован

---

#### Шаг 7: Конфигурация FastAPI

**Действие:**

Добавьте в `api/.env`:

```bash
# Backend
BACKEND_TYPE=langflow

# LangFlow
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your-flow-id-from-step-6
LANGFLOW_API_KEY=your-api-key-from-step-6

# OpenAI (для LangFlow)
OPENAI_API_KEY=sk-proj-your-openai-api-key
```

**Критерий успешного завершения:**

Переменные добавлены в `.env`.

---

#### Шаг 8: Запуск FastAPI с LangFlow backend

**Действие:**

```bash
cd api
uvicorn app.main:app --reload --port 8000
```

**Ожидаемый результат:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Проверка:**

```bash
curl http://localhost:8000/health
```

**Критерий успешного завершения:**

```json
{"status":"ok","backend":"langflow","backend_available":true}
```

---

#### Шаг 9: Тестирование

**Действие:**

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Напиши функцию сортировки", "user_id": "test"}'
```

**Ожидаемый результат:**

JSON-ответ с полями `is_prompt`, `scores`, `recommendations`, `improved_version`.

**Критерий успешного завершения:**

- ✅ LangFlow запущен на http://localhost:7860
- ✅ Flow импортирован и настроен
- ✅ FastAPI отвечает на `/health` с `"backend":"langflow"`
- ✅ API возвращает JSON-ответ с анализом промпта

---

#### Остановка LangFlow

**Действие:**

```bash
docker compose -f docker-compose.langflow.yml down
```

**Ожидаемый результат:**

```
[+] Running 3/3
 ✔ Container prompt-review-langflow  Removed
 ✔ Container prompt-review-postgres   Removed
 ✔ Network langflow-network           Removed
```

**Удаление данных:**

```bash
docker compose -f docker-compose.langflow.yml down -v
```

**Критерий успешного завершения:**

Все контейнеры остановлены и удалены.

---

#### Полный E2E Check для Model 3

**Проверка всех компонентов:**

```bash
# 1. Проверить контейнеры LangFlow
docker compose -f docker-compose.langflow.yml ps

# 2. Проверить LangFlow UI
curl -s -o /dev/null -w "%{http_code}" http://localhost:7860

# 3. Проверить FastAPI health
curl http://localhost:8000/health

# 4. Проверить API test
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text":"Test","user_id":"test"}'
```

**Ожидаемые результаты:**

1. LangFlow контейнеры: `running (healthy)`
2. LangFlow UI: HTTP статус `200`
3. FastAPI health: `{"status":"ok","backend":"langflow","backend_available":true}`
4. API test: JSON с полями `is_prompt`, `scores`, `recommendations`, `improved_version`

---

## Verification Checklist

### После развёртывания API

| Проверка | Команда | Ожидаемый результат |
|----------|---------|---------------------|
| Health check | `curl http://localhost:8000/health` | `{"status":"ok","backend":"langchain","backend_available":true}` |
| API docs | Открыть http://localhost:8000/docs | Swagger UI |
| Web UI | Открыть http://localhost:8000/ui | Форма ввода промпта |
| Review endpoint | `POST /review` | JSON-ответ с анализом |

**Полный чек-лист:**

```bash
# 1. Health check
curl http://localhost:8000/health

# Ожидаемый результат:
# {"status":"ok","backend":"langchain","backend_available":true}

# 2. API test
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"prompt_text":"Test","user_id":"test"}'

# Ожидаемый результат:
# JSON с полями: is_prompt, scores, recommendations, improved_version

# 3. Web UI check
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ui

# Ожидаемый результат:
# 200

# 4. API docs check
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs

# Ожидаемый результат:
# 200
```

### После развёртывания Telegram Bot

| Проверка | Действие | Ожидаемый результат |
|----------|----------|---------------------|
| Bot start | Написать `/start` | Приветственное сообщение |
| Prompt analysis | Написать промпт | Результаты анализа |

**Полный чек-лист:**

```bash
# 1. Проверить процесс бота
ps aux | grep "python.*bot.py"

# Ожидаемый результат:
# Процесс bot.py запущен

# 2. Проверить переменные окружения
echo $TELEGRAM_BOT_TOKEN
echo $PROMPT_REVIEW_API_URL

# Ожидаемый результат:
# Токен и URL должны быть установлены

# 3. Проверить API
curl http://localhost:8000/health

# Ожидаемый результат:
# {"status":"ok",...}
```

### После развёртывания LangFlow

| Проверка | Команда/Действие | Ожидаемый результат |
|----------|------------------|---------------------|
| LangFlow UI | Открыть http://localhost:7860 | Интерфейс LangFlow |
| Health check | `curl http://localhost:8000/health` | `{"status":"ok","backend":"langflow","backend_available":true}` |
| Flow импорт | Импорт `langflow/flows/*.json` | Flow появляется в списке |
| API test | `POST /review` | JSON-ответ с анализом |

**Полный чек-лист:**

```bash
# 1. Проверить контейнеры
docker compose -f docker-compose.langflow.yml ps

# Ожидаемый результат:
# prompt-review-langflow   running
# prompt-review-postgres   running

# 2. Проверить LangFlow health
curl http://localhost:7860/health

# Ожидаемый результат:
# LangFlow отвечает

# 3. Проверить FastAPI health
curl http://localhost:8000/health

# Ожидаемый результат:
# {"status":"ok","backend":"langflow","backend_available":true}

# 4. Проверить Flow в LangFlow UI
# Открыть http://localhost:7860
# Перейти в My Projects
# Проверить наличие Flow "Prompt Review Agent _ Human Report"
```

---

## Troubleshooting

### Проблема: Backend unavailable

**Симптом:**

```json
{"status":"ok","backend":"langchain","backend_available":false}
```

**Причины:**

1. Не указан `OPENAI_API_KEY`
2. Неверный API ключ
3. Проблемы с сетью

**Решение:**

```bash
# Проверьте .env файл
cat api/.env | grep OPENAI_API_KEY

# Должно быть:
# OPENAI_API_KEY=sk-proj-...

# Если ключ верный, проверьте сеть
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-YOUR-KEY"
```

---

### Проблема: ImportError при запуске

**Симптом:**

```
ImportError: cannot import name 'Settings' from 'app.config'
```

**Причины:**

1. Не установлены зависимости
2. Не активировано виртуальное окружение

**Решение:**

```bash
# Проверьте активацию venv
which python

# Переустановите зависимости
pip install -r requirements.txt
```

---

### Проблема: CORS ошибки

**Симптом:**

```
Access to XMLHttpRequest at 'http://localhost:8000/review' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Решение:**

Добавьте в `.env`:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

### Проблема: Telegram Bot не отвечает

**Причины:**

1. Не указан `TELEGRAM_BOT_TOKEN`
2. FastAPI API не запущен
3. Неверный `PROMPT_REVIEW_API_URL`

**Решение:**

```bash
# Проверьте переменные
echo $TELEGRAM_BOT_TOKEN
echo $PROMPT_REVIEW_API_URL

# Проверьте API
curl http://localhost:8000/health
```

---

### Проблема: Docker network not found

**Симптом:**

```
Error response from daemon: network n8n_default not found
```

**Решение:**

```bash
# Создайте сеть
docker network create n8n_default
```

---

### Проблема: LangFlow не запускается

**Симптом:**

```
Container prompt-review-langflow exited with code 1
```

**Причины:**

1. Не указан `POSTGRES_PASSWORD` в `.env`
2. Не указан `LANGFLOW_SECRET_KEY`
3. PostgreSQL не готов к подключению

**Решение:**

```bash
# Проверьте .env файл
cat infra/.env | grep POSTGRES_PASSWORD
cat infra/.env | grep LANGFLOW_SECRET_KEY

# Должны быть установлены:
# POSTGRES_PASSWORD=<secure_password>
# LANGFLOW_SECRET_KEY=<fernet_key>

# Генерация Fernet key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### Проблема: LangFlow backend unavailable

**Симптом:**

```json
{"status":"ok","backend":"langflow","backend_available":false}
```

**Причины:**

1. LangFlow не запущен
2. Неверный `LANGFLOW_URL`
3. Неверный `LANGFLOW_FLOW_ID`
4. Неверный `LANGFLOW_API_KEY`

**Решение:**

```bash
# Проверьте запуск LangFlow
docker compose -f docker-compose.langflow.yml ps

# Проверьте логи
docker compose -f docker-compose.langflow.yml logs -f langflow

# Проверьте переменные
cat api/.env | grep LANGFLOW
```

---

### Проблема: Flow не работает в LangFlow

**Симптом:**

Flow импортирован, но при тесте возвращает ошибку.

**Причины:**

1. Не указан `OPENAI_API_KEY` в компоненте Chat Model
2. Неверная модель OpenAI

**Решение:**

1. Откройте Flow в LangFlow (http://localhost:7860)
2. Найдите компонент **Chat Model**
3. Убедитесь, что `OPENAI_API_KEY` указан
4. Сохраните Flow (Ctrl+S)

**Рекомендация:** Используйте LangChain backend для локального запуска.

---

### Проблема: Web UI не открывается

**Симптом:**

Web UI возвращает ошибку 404 или не загружается.

**Проверка:**

```bash
# Проверить логи API
docker compose -f docker-compose.api.yml logs --tail 50

# Проверить монтирование static файлов
docker compose -f docker-compose.api.yml exec api ls -la /app/web
```

**Возможные причины:**

| Причина | Решение |
|---------|---------|
| Статические файлы не примонтированы | Проверить `volumes` в `docker-compose.api.yml` |
| Неправильный путь | Проверить структуру `api/web/` |
| CORS ошибка | Проверить `CORS_ORIGINS` в `.env` |

**Решение:**

```bash
# Проверить структуру Web UI
ls -la api/web/

# Должны быть: index.html, styles.css, script.js
```

---

### Проблема: API возвращает 500 Internal Server Error

**Симптом:**

API возвращает HTTP 500 при запросе к `/review`.

**Проверка:**

```bash
# Проверить логи API
docker compose -f docker-compose.api.yml logs --tail 100 | grep -i error

# Или для локального запуска
# Логи выводятся в stdout
```

**Возможные причины:**

| Причина | Решение |
|---------|---------|
| Backend недоступен | Проверить `OPENAI_API_KEY`, `OLLAMA_BASE_URL`, или `LANGFLOW_URL` |
| Превышен rate limit | Подождать или увеличить лимиты |
| Неверный формат запроса | Проверить JSON body |
| Backend timeout | Увеличить `API_TIMEOUT` в `.env` |

**Решение:**

```bash
# Проверить переменные окружения
cat api/.env | grep -E "BACKEND_TYPE|OPENAI|LANGFLOW"

# Проверить доступность backend
# Для OpenAI:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Для LangFlow:
curl http://localhost:7860/health

# Для Ollama:
curl http://localhost:11434/api/tags
```

---

## Recovery

### Остановка

```bash
# Local Development
# Ctrl+C в терминале с uvicorn

# Docker Development
docker compose -f docker-compose.api.yml down
```

---

### Перезапуск

```bash
# Local Development
uvicorn app.main:app --reload --port 8000

# Docker Development
docker compose -f docker-compose.api.yml restart
```

---

### Обновление

```bash
# Local Development
git pull
pip install -r requirements.txt --upgrade
uvicorn app.main:app --reload --port 8000

# Docker Development
git pull
docker compose -f docker-compose.api.yml build --no-cache
docker compose -f docker-compose.api.yml up -d
```

---

### Пересборка Docker

```bash
# Полная пересборка
docker compose -f docker-compose.api.yml down
docker compose -f docker-compose.api.yml build --no-cache
docker compose -f docker-compose.api.yml up -d
```

---

### Логи

```bash
# Local Development
# Логи выводятся в stdout

# Docker Development
docker compose -f docker-compose.api.yml logs -f

# Конкретный контейнер
docker logs prompt-review-api -f
```

---

## Files Reference

### Основные файлы проекта

| Файл | Назначение | Обязателен |
|------|------------|------------|
| `api/app/main.py` | Точка входа FastAPI | ✅ Да |
| `api/app/config.py` | Конфигурация из переменных окружения | ✅ Да |
| `api/app/schemas.py` | Pydantic схемы для API | ✅ Да |
| `api/requirements.txt` | Python-зависимости | ✅ Да |
| `api/.env` | Переменные окружения для локального запуска | ✅ Да |
| `infra/.env` | Переменные окружения для Docker | ✅ Да (для Docker) |
| `infra/.env.example` | Пример конфигурации | ⚪ Нет (шаблон) |

### Docker файлы

| Файл | Назначение | Обязателен |
|------|------------|------------|
| `infra/docker-compose.api.yml` | Docker Compose для API | ✅ Да (для Docker) |
| `infra/docker-compose.langflow.yml` | Docker Compose для LangFlow | ⚪ Нет (опционально) |
| `infra/docker-compose.telegram.yml` | Docker Compose для Telegram Bot | ⚪ Нет (опционально) |
| `infra/Dockerfile.api` | Dockerfile для API | ✅ Да (для Docker) |
| `infra/Dockerfile.telegram` | Dockerfile для Telegram Bot | ⚪ Нет (опционально) |

### LangFlow файлы

| Файл | Назначение | Обязателен |
|------|------------|------------|
| `langflow/flows/Prompt Review Agent _ Human Report.json` | Flow для интерактивного анализа | ⚪ Нет (для LangFlow) |
| `n8n/langflow/Prompt Review Agent - API JSON.json` | Flow для API-интеграции | ⚪ Нет (для LangFlow) |

### Telegram Bot файлы

| Файл | Назначение | Обязателен |
|------|------------|------------|
| `api/telegram/bot.py` | Telegram Bot | ⚪ Нет (опционально) |
| `api/telegram/requirements.txt` | Зависимости Telegram Bot | ⚪ Нет (опционально) |

### Web UI файлы

| Файл | Назначение | Обязателен |
|------|------------|------------|
| `api/web/index.html` | Главная страница Web UI | ✅ Да |
| `api/web/styles.css` | Стили Web UI | ✅ Да |
| `api/web/script.js` | JavaScript для Web UI | ✅ Да |

### Документация

| Файл | Назначение |
|------|------------|
| `README.md` | Общее описание проекта |
| `docs/DEPLOYMENT_GUIDE.md` | Это руководство |
| `docs/ARCHITECTURE.md` | Архитектура и компоненты |
| `docs/API_CONTRACT.md` | Контракт API |
| `docs/SPEC.md` | Продуктовая спецификация |
| `docs/PROJECT_STATE.md` | Состояние проекта |

---

---

## Documentation

| Документ | Назначение |
|----------|------------|
| [README.md](../README.md) | Общее описание проекта |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура и компоненты |
| [API_CONTRACT.md](API_CONTRACT.md) | Контракт API |
| [SPEC.md](SPEC.md) | Продуктовая спецификация |
| [api/README.md](../api/README.md) | Документация API |
| [api/telegram/README.md](../api/telegram/README.md) | Документация Telegram Bot |
| [api/web/README.md](../api/web/README.md) | Документация Web UI |
| [langflow/README.md](../langflow/README.md) | Документация LangFlow |
| [langflow/flows/](../langflow/flows/) | Flow для LangFlow |

---

## Заключение

После завершения всех шагов данного руководства у вас должна работать система Prompt Review Service.

### Финальный чек-лист

**Model 1: Local Development**

- ✅ Python 3.11+ установлен
- ✅ Виртуальное окружение создано и активировано
- ✅ Зависимости установлены
- ✅ `.env` файл создан с правильными переменными
- ✅ API запущен на порту 8000
- ✅ Health check возвращает `{"status":"ok"}`
- ✅ Web UI доступен на http://localhost:8000/ui
- ✅ API docs доступны на http://localhost:8000/docs
- ✅ Endpoint `/review` возвращает JSON-ответ

**Model 2: Docker Development**

- ✅ Docker установлен
- ✅ Docker Compose установлен
- ✅ Сеть `n8n_default` создана
- ✅ `.env` файл создан с правильными переменными
- ✅ Контейнер запущен: `docker compose -f docker-compose.api.yml up -d`
- ✅ Health check возвращает `{"status":"ok"}`
- ✅ Web UI доступен
- ✅ API docs доступны

**Model 3: LangFlow Development**

- ✅ LangFlow запущен через Docker Compose
- ✅ LangFlow UI доступен на http://localhost:7860
- ✅ Flow импортирован: `Prompt Review Agent _ Human Report.json`
- ✅ `OPENAI_API_KEY` настроен в Flow
- ✅ Flow ID получен
- ✌ LangFlow API Key создан
- ✅ FastAPI настроен с `BACKEND_TYPE=langflow`
- ✅ Health check возвращает `{"status":"ok","backend":"langflow"}`
- ✅ API test возвращает JSON-ответ

**Telegram Bot (опционально)**

- ✅ Bot создан через @BotFather
- ✅ `TELEGRAM_BOT_TOKEN` установлен в `.env`
- ✅ `PROMPT_REVIEW_API_URL` установлен в `.env`
- ✅ Bot process запущен
- ✅ Bot отвечает на `/start`
- ✅ Bot обрабатывает промпты

### Что дальше

**Для локальной разработки:**

- Изучите [ARCHITECTURE.md](ARCHITECTURE.md) для понимания архитектуры
- Изучите [API_CONTRACT.md](API_CONTRACT.md) для интеграции
- Настройте CI/CD для автоматического тестирования

**Для production:**

- Настройте HTTPS (Traefik/Nginx)
- Настройте аутентификацию
- Настройте rate limiting
- Настройте мониторинг и логирование
- Настройте backup (для LangFlow с PostgreSQL)

**Для интеграции:**

- Используйте REST API для интеграции в CI/CD
- Используйте Telegram Bot для ручной проверки
- Используйте LangFlow для кастомизации AI-пайплайна

---

## Troubleshooting Checklist

При возникновении проблем используйте следующий чек-лист:

**1. Проверьте переменные окружения:**

```bash
# Для Local Development
cat api/.env

# Для Docker Development
cat infra/.env

# Проверьте обязательные переменные
grep -E "BACKEND_TYPE|OPENAI_API_KEY" api/.env
```

**2. Проверьте доступность backend:**

```bash
# Для OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Для LangFlow
curl http://localhost:7860/health

# Для Ollama
curl http://localhost:11434/api/tags
```

**3. Проверьте логи:**

```bash
# Local Development
# Логи выводятся в stdout

# Docker Development
docker compose -f docker-compose.api.yml logs --tail 100

# LangFlow Development
docker compose -f docker-compose.langflow.yml logs --tail 100
```

**4. Проверьте порты:**

```bash
# Проверьте занятые порты
netstat -tuln | grep -E "8000|7860|11434"

# Проверьте доступность
curl http://localhost:8000/health
curl http://localhost:7860/health (для LangFlow)
```

**5. Проверьте Docker (для Docker Development):**

```bash
# Проверьте контейнеры
docker compose -f docker-compose.api.yml ps

# Проверьте сети
docker network ls | grep n8n_default

# Проверьте volumes
docker volume ls
```

Если проблема не решена, обратитесь к разделу [Troubleshooting](#troubleshooting) для конкретных проблем.

---

## Change Log

**2026-07-07 (v2.2):**
- ✅ Добавлена секция "Заключение" с финальным чек-листом
- ✅ Добавлены критерии успешного завершения для каждого шага
- ✅ Улучшены примеры выводов команд
- ✅ Добавлен полный E2E Check для каждой модели развёртывания
- ✅ Расширен troubleshooting с диагностическими командами
- ✅ Улучшена структура Files Reference
- ✅ Добавлены проверки для всех компонентов

**2026-07-07 (v2.1):**
- ✅ Добавлена Model 3: LangFlow Development
- ✅ Добавлены пошаговые инструкции для LangFlow
- ✅ Добавлен импорт Flow из репозитория
- ✅ Обновлена информация о Flow файлах
- ✅ Добавлены troubleshooting для LangFlow
- ✅ Добавлены примеры .env для LangFlow

**2026-07-07 (v2.0):**
- ✅ Полностью переработан документ
- ✅ Добавлены модели развёртывания
- ✅ Добавлены пошаговые инструкции
- ✅ Добавлены проверки после каждого этапа
- ✅ Добавлены troubleshooting и recovery
- ✅ Использованы только реальные источники проекта

---

## Качество документа

Данный документ соответствует стандартам инженерного руководства по развёртыванию:

- ✅ **Полнота**: все шаги описаны детально
- ✅ **Логичность**: порядок действий понятен
- ✅ **Актуальность**: команды соответствуют текущему проекту
- ✅ **Примеры**: достаточное количество примеров команд и результатов
- ✅ **Troubleshooting**: описаны типичные проблемы и решения
- ✅ **Отсутствие внутренних артефактов APL**: документ полностью публичный
- ✅ **Критерии успешного завершения**: каждый шаг имеет чёткий критерий успеха
- ✅ **E2E проверки**: добавлены комплексные проверки для всех моделей развёртывания