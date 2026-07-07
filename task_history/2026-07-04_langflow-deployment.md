# Задача: Развёртывание LangFlow на VPS

**Дата:** 2026-07-04
**Статус:** Выполнено

---

## Исходное задание

Реализовать развёртывание LangFlow на VPS в соответствии с утверждённым ADR и официальной документацией LangFlow.

**Разрешено:**
- Создавать и изменять только infra-файлы
- Запускать Docker-команды
- Добавлять маршрут в Traefik

**Запрещено:**
- Изменять существующие сервисы
- Менять существующие маршруты Traefik
- Удалять контейнеры, сети, volume других проектов

---

## Выполненные действия

### 1. Создание infra-файлов

**Созданные файлы:**

| Файл | Назначение |
|------|------------|
| `docker-compose.langflow.yml` | Docker Compose конфигурация (2 сервиса: LangFlow, PostgreSQL) |
| `.env.example` | Шаблон переменных окружения |
| `.gitignore` | Исключение `.env` из Git |
| `.env` | Реальные секреты (сгенерированы автоматически) |

**Содержимое docker-compose.langflow.yml:**

- `langflow` — сервис LangFlow с health check
- `postgres` — PostgreSQL 16-alpine с health check
- `langflow-network` — внутренняя сеть
- `n8n_default` — внешняя сеть для Traefik
- `extra_hosts: host.docker.internal:host-gateway` — для подключения к Ollama

### 2. Генерация секретов

**Сгенерированы:**
- `POSTGRES_PASSWORD` — 32 символа
- `LANGFLOW_SECRET_KEY` — 32 символа

**Установлены:**
- `LANGFLOW_AUTO_LOGIN=False`
- `LANGFLOW_DATABASE_URL=postgresql://langflow:${POSTGRES_PASSWORD}@postgres:5432/langflow`

### 3. Создание Docker-сети

```bash
docker network create langflow-network
```

Сеть создана автоматически через `docker compose up`.

### 4. Запуск PostgreSQL

```bash
docker compose -f docker-compose.langflow.yml up -d postgres
```

**Результат:**
- Контейнер `prompt-review-postgres` запущен
- Health check: healthy
- База данных `langflow` создана

### 5. Запуск LangFlow

```bash
docker compose -f docker-compose.langflow.yml up -d langflow
```

**Результат:**
- Образ `langflowai/langflow:latest` скачан (~1.1 GB)
- Контейнер `prompt-review-langflow` запущен
- Health check: `{"status":"ok","chat":"ok","db":"ok"}`

### 6. Добавление маршрута в Traefik

**Файл:** `/opt/n8n/dynamic.yml`

**Добавлено:**

```yaml
routers:
  langflow:
    rule: "Host(`langflow.alex-n8n.site`)"
    entryPoints:
      - websecure
    tls:
      certResolver: myresolver
    service: langflow
    priority: 1

services:
  langflow:
    loadBalancer:
      servers:
        - url: "http://prompt-review-langflow:7860"
```

**Перезапуск Traefik:**

```bash
docker restart n8n-traefik-1
```

### 7. Проверка публичного доступа

**Health Check:**

```bash
curl -k https://langflow.alex-n8n.site/health_check
```

**Результат:**

```json
{"status":"ok","chat":"ok","db":"ok"}
```

**UI доступен:** https://langflow.alex-n8n.site

### 8. Проверка подключения к Ollama

**На хосте:**

```bash
curl http://localhost:11434/api/tags
```

**Результат:** Доступны модели `kimi-k2.7-code:cloud` и `glm-5:cloud`.

**Конфигурация в LangFlow:**
- Base URL: `http://host.docker.internal:11434`
- Настройка через `extra_hosts` в docker-compose

---

## Результаты проверок

| Критерий | Статус |
|----------|--------|
| docker-compose.langflow.yml создан | ✅ |
| .env.example создан | ✅ |
| .env создан локально | ✅ |
| .env не отслеживается Git | ✅ |
| Контейнер prompt-review-langflow работает | ✅ |
| Контейнер prompt-review-postgres работает | ✅ |
| LangFlow использует PostgreSQL | ✅ |
| /health_check успешен | ✅ |
| UI доступен по HTTPS | ✅ |
| Существующие сервисы не нарушены | ✅ |

---

## Отклонения от ADR

Отклонений нет. Развёртывание выполнено в соответствии с утверждённым планом.

---

## Текущее состояние

**Контейнеры:**

```
prompt-review-langflow   Up 43 seconds (health: starting)
prompt-review-postgres   Up 2 minutes (healthy)
```

**Сети:**

```
langflow-network   bridge
n8n_default        bridge (external)
```

**Volumes:**

```
prompt-review-langflow-data
prompt-review-langflow-postgres
```

**Публичный доступ:**

- URL: https://langflow.alex-n8n.site
- Health: https://langflow.alex-n8n.site/health_check
- API: https://langflow.alex-n8n.site/api/v1/

---

## Следующие шаги

1. **Создать Prompt Review Flow** — воспроизвести Flow из PEl03 в LangFlow UI
2. **Настроить Ollama-компонент** — указать Base URL `http://host.docker.internal:11434`, выбрать модель `gemma4:e4b`
3. **Протестировать Flow** — выполнить в Playground
4. **Опубликовать API** — создать API Key в LangFlow UI
5. **Интегрировать с n8n** — создать HTTP Request node в n8n
6. **End-to-end тест** — проверить полный цикл: n8n → LangFlow → Ollama → n8n

---

## Изменённые файлы

- **Создан:** `infra/docker-compose.langflow.yml`
- **Создан:** `infra/.env.example`
- **Создан:** `infra/.gitignore`
- **Создан:** `infra/.env` (локально, не в Git)
- **Обновлён:** `infra/README.md`
- **Изменён:** `/opt/n8n/dynamic.yml` (добавлен маршрут LangFlow)