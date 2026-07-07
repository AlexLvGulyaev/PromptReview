# Infrastructure

Инфраструктурные конфигурации для Prompt Review Service.

## Статус

**LangFlow, FastAPI и Telegram Bot развёрнуты и работают.**

## Развернутые компоненты

| Компонент | Контейнер | Статус |
|-----------|-----------|--------|
| LangFlow | `prompt-review-langflow` | Работает |
| PostgreSQL | `prompt-review-postgres` | Работает (healthy) |
| FastAPI API | `prompt-review-api` | Работает |
| Telegram Bot | `prompt-review-telegram` | Работает |

## Компоненты

### LangFlow

- **UI:** Доступен после локального развёртывания (см. DEPLOYMENT_GUIDE.md)
- **Health Check:** `/health_check`
- **API:** `/api/v1/`

### Prompt Review API

- **API Root:** Доступен после локального развёртывания (см. DEPLOYMENT_GUIDE.md)
- **Health:** `/health`
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **Review Endpoint:** `/review` (POST)

### Web UI

- **Demo:** Доступен после локального развёртывания (см. DEPLOYMENT_GUIDE.md)

### Telegram Bot

- **Bot:** Требует собственного bot token (см. DEPLOYMENT_GUIDE.md)
- **Commands:** `/start`, `/help`
- **Usage:** Отправьте текст для анализа качества промпта

## Файлы

| Файл | Назначение |
|------|------------|
| `docker-compose.langflow.yml` | LangFlow + PostgreSQL |
| `docker-compose.api.yml` | FastAPI API Service |
| `docker-compose.telegram.yml` | Telegram Bot Service |
| `Dockerfile.api` | Dockerfile для FastAPI |
| `Dockerfile.telegram` | Dockerfile для Telegram Bot |
| `.env.example` | Шаблон переменных окружения |
| `.env` | Реальные секреты (не в Git) |
| `.gitignore` | Исключения для Git |

## Переменные окружения

Созданы безопасные значения для:
- `POSTGRES_PASSWORD` — пароль PostgreSQL
- `LANGFLOW_SECRET_KEY` — секретный ключ JWT
- `LANGFLOW_AUTO_LOGIN=False` — аутентификация включена

## Сети

| Сеть | Назначение |
|------|------------|
| `langflow-network` | Внутренняя сеть LangFlow ↔ PostgreSQL |
| `n8n_default` | Сеть Traefik для публикации |

## Маршрутизация

Маршрут добавлен в `/opt/n8n/dynamic.yml`:

```yaml
routers:
  langflow:
    rule: "Host(`langflow.your-domain.com`)"
    entryPoints:
      - websecure
    tls:
      certResolver: myresolver
    service: langflow

services:
  langflow:
    loadBalancer:
      servers:
        - url: "http://prompt-review-langflow:7860"
```

## Ollama

LangFlow подключается к Ollama через `host.docker.internal:11434`.

Доступные модели:
- `kimi-k2.7-code:cloud`
- `glm-5:cloud`

---

## FastAPI → LangFlow Integration

Для работы FastAPI с LangFlow backend требуются переменные окружения:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BACKEND_TYPE` | Тип backend | `langflow` или `langchain` |
| `LANGFLOW_URL` | URL LangFlow сервера | `http://localhost:7860` |
| `LANGFLOW_FLOW_ID` | ID Flow в LangFlow | `eaa36f47-604c-4c62-902b-d4c84ffde61a` |
| `LANGFLOW_API_KEY` | API ключ LangFlow | (секрет, не в Git) |

### Получение LangFlow API Key

1. Открыть LangFlow UI (см. DEPLOYMENT_GUIDE.md)
2. Перейти в **Settings** (иконка шестерёнки)
3. Выбрать **API Keys**
4. Нажать **Create API Key**
5. Скопировать созданный ключ
6. Добавить в `infra/.env`:

   ```bash
   LANGFLOW_API_KEY=скопированный_ключ
   ```

### Хранение секретов

- **Шаблон без секретов:** `infra/.env.example` (в Git)
- **Реальные секреты:** `infra/.env` (НЕ в Git, в `.gitignore`)
- **FastAPI читает:** переменные из `infra/.env` при запуске

---

## Следующие шаги

1. ~~Создать Prompt Review Flow в LangFlow UI~~ ✅ Готово
2. ~~Настроить Ollama-компонент в Flow~~ ✅ Готово
3. ~~Опубликовать API~~ ✅ Готово
4. ~~Интегрировать с n8n~~ ✅ Готово
5. ~~Получить API Key из LangFlow UI~~ ✅ Готово
6. ~~Добавить ключ в `infra/.env`~~ ✅ Готово
7. ~~Развёртывание FastAPI~~ ✅ Готово

---

## Развёртывание FastAPI

### Предварительные требования

1. LangFlow уже развёрнут и работает
2. Переменные окружения в `.env` настроены
3. API ключ LangFlow добавлен

### Запуск

```bash
cd /opt/ai-automation-portfolio-lab/cases/prompt-review/infra

# Сборка и запуск
docker compose -f docker-compose.api.yml up -d --build

# Проверка логов
docker compose -f docker-compose.api.yml logs -f

# Проверка статуса
docker compose -f docker-compose.api.yml ps
```

### Маршрутизация Traefik

Для публикации через Traefik добавьте маршрут в `/opt/n8n/dynamic.yml`:

```yaml
http:
  routers:
    prompt-review-api:
      rule: "Host(`api.your-domain.com`)"
      entryPoints:
        - websecure
      tls:
        certResolver: myresolver
      service: prompt-review-api

    prompt-review-demo:
      rule: "Host(`demo.your-domain.com`)"
      entryPoints:
        - websecure
      tls:
        certResolver: myresolver
      service: prompt-review-demo

  services:
    prompt-review-api:
      loadBalancer:
        servers:
          - url: "http://prompt-review-api:8000"

    prompt-review-demo:
      loadBalancer:
        servers:
          - url: "http://prompt-review-api:8000"
```

После изменения конфигурации Traefik:

```bash
# Перезагрузка Traefik
docker restart n8n-traefik
```

### Проверка

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Web UI
open http://localhost:8000/ui
```

---

## Развёртывание Telegram Bot

### Запуск

```bash
cd /opt/ai-automation-portfolio-lab/cases/prompt-review/infra

# Сборка и запуск
docker compose -f docker-compose.telegram.yml up -d --build

# Проверка логов
docker compose -f docker-compose.telegram.yml logs -f

# Проверка статуса
docker compose -f docker-compose.telegram.yml ps
```

### Конфигурация

Telegram Bot читает переменные из `.env`:

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | ✅ Да |
| `PROMPT_REVIEW_API_URL` | URL FastAPI API | Нет (default: Docker network) |
| `API_TIMEOUT` | Таймаут API (секунды) | Нет (default: 60) |

В Docker используется внутренний URL: `http://prompt-review-api:8000`

### Проверка

```bash
# Логи бота
docker logs prompt-review-telegram --tail 20

# Должно показать:
# - Starting Prompt Review Telegram Bot
# - API health check: {'status': 'ok', ...}
```

---

## Безопасность

### CORS

FastAPI настроен с CORS для доверенных origin:

- `http://localhost:3000` — разработка
- `http://localhost:8000` — локальный API
- Другие origins настраиваются через `CORS_ORIGINS`

Telegram Bot работает через server-to-server и не требует CORS.

### Секреты

Все секреты хранятся в `infra/.env`:
- `POSTGRES_PASSWORD`
- `LANGFLOW_SECRET_KEY`
- `LANGFLOW_API_KEY`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`

Файл `.env` добавлен в `.gitignore` и **не коммитится в Git**.

### HTTPS

Весь публичный трафик идёт через Traefik с автоматическим HTTPS (Let's Encrypt).

---

## Мониторинг

### Health Checks

Все сервисы имеют health check:

```bash
# LangFlow
curl http://localhost:7860/health_check

# FastAPI
curl http://localhost:8000/health
```

### Логирование

FastAPI использует структурированное JSON-логирование:

```json
{
  "timestamp": "2026-07-06T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Review request received",
  "request_id": "req_123456",
  "user_id": "telegram:123456789",
  "source": "telegram",
  "prompt_length": 150,
  "processing_time_ms": 2500
}
```

**Важно:** Полный текст промпта не логируется (только длина).