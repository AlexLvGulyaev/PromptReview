# LangFlow APL Integration Plan

Architecture Decision Record (ADR) для интеграции LangFlow в инфраструктуру AI Automation Portfolio Lab.

---

## 1. Общая архитектура

### Место LangFlow в инфраструктуре APL

```mermaid
flowchart TB
    Internet[Internet] --> Traefik[Traefik v3.3<br/>n8n_default]
    Traefik --> |langflow.alex-n8n.site| LangFlow[LangFlow<br/>7860]
    Traefik --> |n8n-de.alex-n8n.site| HRN8n[HR Assistant n8n]
    Traefik --> |lead-qual.alex-n8n.site| LeadN8n[Lead Qualification n8n]

    LangFlow --> |host.docker.internal:11434| Ollama[Ollama<br/>localhost:11434]
    LangFlow --> |langflow-network| LangFlowDB[(PostgreSQL<br/>langflow_db)]

    LeadN8n --> |HTTP API| LangFlow
    HRN8n --> |HTTP API| LangFlow

    subgraph VPS [VPS Infrastructure]
        Traefik
        LangFlow
        Ollama
        LangFlowDB
        HRN8n
        LeadN8n
    end
```

### Компоненты интеграции

| Компонент | Роль | Взаимодействие |
|-----------|------|----------------|
| **Traefik** | Reverse proxy, SSL termination | Маршрутизация на LangFlow по Host |
| **LangFlow** | AI Flow платформа | Выполнение Prompt Review Flow |
| **Ollama** | LLM inference | Модели gemma4:e4b, kimi-k2.7-code |
| **n8n** | Оркестратор | HTTP Request к LangFlow API |
| **PostgreSQL** | Persistence LangFlow | Отдельная база langflow_db |

### Поток данных

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant N8n as n8n
    participant LF as LangFlow
    participant Ollama as Ollama

    User->>N8n: Отправка промпта
    N8n->>LF: POST /api/v1/run/{flow_id}
    LF->>LF: Загрузка Prompt Review Flow
    LF->>Ollama: Запрос к модели
    Ollama-->>LF: Ответ модели
    LF->>LF: Анализ результата
    LF-->>N8n: JSON ответ
    N8n-->>User: Результат ревью
```

---

## 2. Выбранный способ развёртывания

### Решение

**Использовать адаптированную конфигурацию Docker Compose.**

Не использовать официальный production compose полностью.

### Обоснование

| Критерий | Официальный compose | Адаптированный compose |
|----------|-------------------|----------------------|
| Сложность | 11 сервисов (Traefik, backend, frontend, db, broker, celery, flower, prometheus, grafana, pgadmin) | 2 сервиса (LangFlow, PostgreSQL) |
| Ресурсы | Высокое потребление (RabbitMQ, Celery workers, monitoring) | Минимальное потребление |
| Traefik | Встроенный | Использовать существующий |
| Назначение | Enterprise production | Single-purpose deployment |

**Факторы решения:**

1. **Существующий Traefik** — уже работает и обслуживает n8n, нет необходимости в дублировании
2. **Отсутствие Celery потребностей** — Prompt Review Flow не требует очередей задач
3. **Минимальные ресурсы** — один Flow не требует мониторинга Prometheus/Grafana
4. **Простота поддержки** — меньше компонентов = меньше точек отказа

### Что берём из официального compose

- Образ `langflowai/langflow:latest` (или конкретная версия)
- Переменные окружения из документации
- Конфигурация PostgreSQL
- Health check `/health_check`

### Что адаптируем

- Убираем встроенный Traefik (используем существующий)
- Убираем RabbitMQ, Celery, Flower (не нужны для одного Flow)
- Убираем Prometheus, Grafana (не нужны на начальном этапе)
- Упрощаем до 2 сервисов: LangFlow + PostgreSQL

---

## 3. База данных

### Решение

**Использовать отдельный PostgreSQL-контейнер с отдельной базой данных.**

Не использовать SQLite. Не использовать существующий экземпляр PostgreSQL.

### Обоснование

#### Почему не SQLite

**Из официальной документации:**

> "When cloning the repo and using Docker Compose, the default deployment uses PostgreSQL instead of the default SQLite database."

**Причины:**
- SQLite не подходит для production
- Отсутствует одновременный доступ
- Нет возможности масштабирования
- Риск потери данных при перезапуске контейнера без volume

#### Почему не существующий PostgreSQL

**Текущая инфраструктура:**

| Контейнер | База данных | Назначение |
|-----------|------------|------------|
| `n8n-postgres_hr-1` | `hr_assistant` | HR Assistant |
| `lead-qualification-postgres` | `n8n`, `lead_qualification` | Lead Qualification |
| `pel-postgres` | PEL базы | Prompt Engineering Lab |
| `review-flow-postgres` | review-flow | Review Flow |
| `portfolio-test-postgres-1` | portfolio | Portfolio Test |

**Риски совместного использования:**
1. Конфликт схем (LangFlow создаёт свои таблицы)
2. Нет изоляции данных
3. Влияние на производительность других проектов
4. Сложность миграций и бэкапов

#### Преимущества отдельного PostgreSQL

- Полная изоляция данных LangFlow
- Независимое масштабирование
- Отдельные бэкапы
- Не влияет на другие проекты APL
- Соответствует официальной рекомендации

### Конфигурация PostgreSQL

```yaml
postgres:
  image: postgres:16-alpine
  container_name: prompt-review-postgres
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: langflow
  volumes:
    - langflow-postgres:/var/lib/postgresql/data
  networks:
    - langflow-network
```

---

## 4. Docker-сети

### Решение

**Создать отдельную сеть `langflow-network` + подключиться к `n8n_default`.**

### Обоснование

#### Создаваемые сети

| Сеть | Назначение |
|------|------------|
| `langflow-network` | Внутренняя сеть LangFlow (backend + postgres) |

#### Переиспользуемые сети

| Сеть | Назначение |
|------|------------|
| `n8n_default` | Сеть Traefik для публикации сервисов |

#### Почему не только `n8n_default`

**Изоляция:** LangFlow и PostgreSQL общаются во внутренней сети `langflow-network`. Только LangFlow подключён к `n8n_default` для публикации через Traefik.

**Безопасность:** PostgreSQL не доступен из `n8n_default`, только из `langflow-network`.

### Конфигурация сетей

```yaml
networks:
  langflow-network:
    driver: bridge
    name: langflow-network
  n8n_default:
    external: true
    name: n8n_default
```

### Публикация через Traefik

**Маршрут в `/opt/n8n/dynamic.yml`:**

```yaml
routers:
  langflow:
    rule: "Host(`langflow.alex-n8n.site`)"
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

**LangFlow контейнер подключается к `n8n_default`:**

```yaml
langflow:
  networks:
    - langflow-network
    - n8n_default
```

---

## 5. Поддомен

### Решение

**Утверждённый поддомен: `langflow.alex-n8n.site`**

### Обоснование

| Критерий | Решение |
|----------|---------|
| Согласованность | Соответствует шаблону `*.alex-n8n.site` |
| Понятность | `langflow` чётко указывает на сервис |
| Уникальность | Не конфликтует с существующими поддоменами |
| Существующие поддомены | `n8n-de`, `lead-qual`, `lead-qual-admin`, `lead-qual-demo` |

### DNS

DNS-запись уже настроена для `*.alex-n8n.site` (wildcard).

Let's Encrypt сертификат автоматически выпускается Traefik при добавлении маршрута.

---

## 6. Структура файлов

### Окончательный состав

```
cases/prompt-review/infra/
├── README.md                          # Общее описание инфраструктуры
├── docker-compose.langflow.yml        # Docker Compose для LangFlow
├── .env.example                       # Шаблон переменных окружения
├── .gitignore                         # Исключения для Git
├── LANGFLOW_VPS_DEPLOYMENT_PLAN.md    # План развёртывания (audit)
├── LANGFLOW_DEPLOYMENT_RESEARCH.md    # Исследование (research)
└── LANGFLOW_APL_INTEGRATION_PLAN.md   # Архитектурное решение (ADR)
```

### Назначение файлов

| Файл | Назначение |
|------|------------|
| `README.md` | Общее описание инфраструктуры кейса |
| `docker-compose.langflow.yml` | Конфигурация сервисов LangFlow и PostgreSQL |
| `.env.example` | Шаблон переменных (без секретов) |
| `.gitignore` | Исключение `.env`, ключей, секретов |
| `LANGFLOW_VPS_DEPLOYMENT_PLAN.md` | Результаты аудита VPS |
| `LANGFLOW_DEPLOYMENT_RESEARCH.md` | Исследование документации LangFlow |
| `LANGFLOW_APL_INTEGRATION_PLAN.md` | Архитектурные решения (этот документ) |

### Содержимое docker-compose.langflow.yml

```yaml
# LangFlow Docker Compose Configuration
# Version: 1.0
# Architecture Decision: Adapted configuration for APL

services:
  langflow:
    image: langflowai/langflow:latest
    container_name: prompt-review-langflow
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - langflow-data:/app/langflow
    ports:
      - "7860:7860"
    networks:
      - langflow-network
      - n8n_default
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:7860/health_check || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  postgres:
    image: postgres:16-alpine
    container_name: prompt-review-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: langflow
    volumes:
      - langflow-postgres:/var/lib/postgresql/data
    networks:
      - langflow-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d langflow"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

networks:
  langflow-network:
    driver: bridge
    name: langflow-network
  n8n_default:
    external: true
    name: n8n_default

volumes:
  langflow-data:
    name: prompt-review-langflow-data
  langflow-postgres:
    name: prompt-review-langflow-postgres
```

### Содержимое .env.example

```bash
# LangFlow Environment Configuration
# Copy to .env and fill in your values

# ============================================================================
# PostgreSQL Configuration
# ============================================================================
POSTGRES_USER=langflow
POSTGRES_PASSWORD=your_secure_password_here

# ============================================================================
# LangFlow Configuration
# ============================================================================

# Server configuration
LANGFLOW_HOST=0.0.0.0
LANGFLOW_PORT=7860

# Database connection
LANGFLOW_DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/langflow

# Security (IMPORTANT: change for production!)
LANGFLOW_AUTO_LOGIN=False
LANGFLOW_SECRET_KEY=your_secret_key_here_minimum_32_characters

# Ollama connection (running on host)
# Use host.docker.internal for Docker on Linux
LANGFLOW_OPENAI_API_BASE=http://host.docker.internal:11434/v1

# Logging
LANGFLOW_LOG_LEVEL=info

# ============================================================================
# Optional: Superuser (for initial setup)
# ============================================================================
# LANGFLOW_SUPERUSER=admin
# LANGFLOW_SUPERUSER_PASSWORD=your_admin_password_here
```

### Содержимое .gitignore

```gitignore
# Environment files with secrets
.env

# API keys
*.key
*.pem

# Logs
*.log

# Local overrides
.env.local
docker-compose.override.yml
```

---

## 7. Хранение секретов

### Решение

**Секреты хранятся в `.env` файле, исключённом из Git.**

### Структура

| Файл | Git | Содержимое |
|------|-----|------------|
| `.env.example` | ✅ Коммитится | Шаблон без секретов |
| `.env` | ❌ Не коммитится | Реальные секреты |
| `.gitignore` | ✅ Коммитится | Правила исключения |

### Переменные окружения

**Обязательно установить:**

| Переменная | Назначение |
|-----------|------------|
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `LANGFLOW_SECRET_KEY` | Секретный ключ JWT (минимум 32 символа) |

**Рекомендуется установить:**

| Переменная | Назначение |
|-----------|------------|
| `LANGFLOW_SUPERUSER` | Имя суперпользователя |
| `LANGFLOW_SUPERUSER_PASSWORD` | Пароль суперпользователя |

### Генерация секретов

```bash
# PostgreSQL password
openssl rand -base64 32

# LangFlow secret key
openssl rand -base64 32
```

### После развертывания

1. Создать API Key в LangFlow UI
2. Сохранить API Key в n8n credentials
3. Не коммитить API Key в Git

---

## 8. Интеграция с Ollama

### Решение

**LangFlow подключается к Ollama через `host.docker.internal:11434`.**

### Обоснование

**Текущее состояние:**
- Ollama установлен на хосте VPS (не в Docker)
- Адрес: `http://localhost:11434`
- Модели: `gemma4:e4b`, `kimi-k2.7-code:cloud`

**Из официальной документации LangFlow:**

> "If running LangFlow in a container while Ollama runs on the host: Use `host.docker.internal:11434` (Docker Desktop) or use `http://<host-ip>:11434` from the container."

**Для Linux:**

`host.docker.internal` работает в Docker 20.10+ с флагом `--add-host`.

Альтернатива: использовать IP-адрес хоста из Docker-сети.

### Конфигурация в LangFlow

**В UI LangFlow:**

1. Добавить компонент Ollama
2. Указать Base URL: `http://host.docker.internal:11434`
3. Нажать Refresh для списка моделей
4. Выбрать модель: `gemma4:e4b`

**Или через переменную окружения:**

```bash
LANGFLOW_OPENAI_API_BASE=http://host.docker.internal:11434/v1
```

### Docker Compose флаг

Для работы `host.docker.internal` на Linux добавить в compose:

```yaml
services:
  langflow:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

---

## 9. Интеграция с n8n

### Архитектурный принцип

**n8n вызывает LangFlow через HTTP API.**

### Поток данных

```
n8n Workflow
    ↓
HTTP Request Node
    ↓
POST /api/v1/run/{flow_id}
    ↓
LangFlow: Prompt Review Flow
    ↓
Ollama: gemma4:e4b
    ↓
JSON Response
    ↓
n8n: обработка результата
```

### Эндпоинты LangFlow API

| Endpoint | Method | Назначение |
|----------|--------|------------|
| `/api/v1/run/{flow_id}` | POST | Выполнение Flow |
| `/health_check` | GET | Health check |
| `/api/v1/flows/` | GET | Список Flow |

### Аутентификация

**Способ:** API Key в заголовке `x-api-key`.

**Процесс:**

1. В LangFlow UI: Settings → Langflow API Keys → Create API Key
2. Сохранить API Key
3. В n8n: Credentials → HTTP Header → `x-api-key: {API_KEY}`

### Формат запроса

```json
{
  "input_value": "Текст промпта для анализа",
  "input_type": "chat",
  "output_type": "chat",
  "tweaks": {}
}
```

### Формат ответа

```json
{
  "session_id": "...",
  "outputs": [
    {
      "inputs": {...},
      "outputs": [
        {
          "results": {
            "message": {
              "text": "Результат анализа промпта..."
            }
          }
        }
      ]
    }
  ]
}
```

### URL для n8n

**Внутри Docker-сети:**

```
http://prompt-review-langflow:7860/api/v1/run/{flow_id}
```

**Или через Traefik (внешний):**

```
https://langflow.alex-n8n.site/api/v1/run/{flow_id}
```

---

## 10. Последовательность внедрения

### Шаг 1: Создание файлов

**Файлы:**
- `infra/docker-compose.langflow.yml`
- `infra/.env.example`
- `infra/.gitignore`

**Проверка:**
- Файлы существуют
- `.gitignore` содержит `.env`

---

### Шаг 2: Создание .env

**Действие:**
```bash
cd /opt/ai-automation-portfolio-lab/cases/prompt-review/infra
cp .env.example .env
# Отредактировать .env: установить пароли
```

**Проверка:**
- `.env` существует
- `.env` не отслеживается Git

---

### Шаг 3: Создание Docker-сети

**Действие:**
```bash
docker network create langflow-network
```

**Проверка:**
```bash
docker network ls | grep langflow-network
```

---

### Шаг 4: Запуск PostgreSQL

**Действие:**
```bash
docker compose -f docker-compose.langflow.yml up -d postgres
```

**Проверка:**
```bash
docker logs prompt-review-postgres
# Дождаться: "database system is ready to accept connections"
```

---

### Шаг 5: Запуск LangFlow

**Действие:**
```bash
docker compose -f docker-compose.langflow.yml up -d langflow
```

**Проверка:**
```bash
docker logs prompt-review-langflow
# Дождаться: "Uvicorn running on http://0.0.0.0:7860"
```

---

### Шаг 6: Проверка Health Check

**Действие:**
```bash
curl http://localhost:7860/health_check
```

**Ожидаемый результат:**
```json
{
  "status": "ok",
  "chat": "ok",
  "db": "ok"
}
```

---

### Шаг 7: Добавление маршрута в Traefik

**Файл:** `/opt/n8n/dynamic.yml`

**Добавить:**
```yaml
routers:
  langflow:
    rule: "Host(`langflow.alex-n8n.site`)"
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

**Проверка:**
```bash
# Перезагрузить Traefik (если требуется)
docker restart n8n-traefik-1

# Проверить DNS
dig langflow.alex-n8n.site

# Проверить HTTPS
curl -k https://langflow.alex-n8n.site/health_check
```

---

### Шаг 8: Проверка UI

**Действие:**
- Открыть `https://langflow.alex-n8n.site`
- Проверить загрузку интерфейса LangFlow

---

### Шаг 9: Создание Prompt Review Flow

**Действие:**
- В LangFlow UI: New Flow
- Добавить компоненты: Chat Input → Ollama → Chat Output
- Настроить Ollama: Base URL `http://host.docker.internal:11434`, Model `gemma4:e4b`
- Настроить системный промпт (из PEl03)
- Сохранить Flow

**Проверка:**
- Открыть Playground
- Протестировать Flow

---

### Шаг 10: Публикация API

**Действие:**
- В LangFlow UI: Settings → Langflow API Keys → Create API Key
- Скопировать Flow ID из URL
- Скопировать API Key

**Проверка:**
```bash
curl -X POST \
  "https://langflow.alex-n8n.site/api/v1/run/{FLOW_ID}?stream=false" \
  -H "Content-Type: application/json" \
  -H "x-api-key: {API_KEY}" \
  -d '{"input_value": "test prompt", "input_type": "chat", "output_type": "chat"}'
```

---

### Шаг 11: Интеграция с n8n

**Действие:**
- В n8n: создать HTTP Request node
- Настроить credentials с API Key
- Протестировать вызов

**Проверка:**
- n8n успешно вызывает LangFlow
- Возвращается корректный JSON

---

## 11. Критерии готовности

### Контейнеризация

| Критерий | Проверка |
|----------|----------|
| PostgreSQL контейнер работает | `docker ps \| grep prompt-review-postgres` |
| LangFlow контейнер работает | `docker ps \| grep prompt-review-langflow` |
| LangFlow health check успешен | `curl http://localhost:7860/health_check` → `{"status": "ok"}` |
| Данные сохраняются после перезапуска | Перезапустить контейнер, проверить Flow в UI |

### Сеть

| Критерий | Проверка |
|----------|----------|
| LangFlow подключён к `n8n_default` | `docker network inspect n8n_default` |
| LangFlow подключён к `langflow-network` | `docker network inspect langflow-network` |
| LangFlow доступен из Traefik | `curl http://prompt-review-langflow:7860/health_check` (из Traefik контейнера) |

### Публикация

| Критерий | Проверка |
|----------|----------|
| DNS резолвится | `dig langflow.alex-n8n.site` |
| HTTPS работает | `curl https://langflow.alex-n8n.site/health_check` |
| SSL сертификат валидный | Проверить в браузере |

### Функциональность

| Критерий | Проверка |
|----------|----------|
| UI доступен | Открыть `https://langflow.alex-n8n.site` |
| Ollama подключена | Создать Flow с Ollama компонентом, выбрать модель |
| Flow создаётся | Создать тестовый Flow |
| Flow выполняется | Запустить Flow в Playground |
| API доступен | Вызвать Flow через curl с API Key |

### Интеграция с n8n

| Критерий | Проверка |
|----------|----------|
| n8n может вызвать LangFlow | HTTP Request node возвращает результат |
| JSON парсится | n8n корректно обрабатывает ответ |
| End-to-end работает | Полный цикл: n8n → LangFlow → Ollama → n8n |

---

## Архитектурные решения (Summary)

| Решение | Выбор | Обоснование |
|---------|-------|-------------|
| **Развёртывание** | Адаптированный compose | Минимальная сложность для одного Flow |
| **База данных** | Отдельный PostgreSQL | Изоляция, масштабируемость |
| **Docker-сети** | `langflow-network` + `n8n_default` | Изоляция + публикация |
| **Поддомен** | `langflow.alex-n8n.site` | Согласованность с APL |
| **Ollama** | `host.docker.internal:11434` | Ollama на хосте |
| **Секреты** | `.env` вне Git | Стандартный подход |
| **API** | `/api/v1/run/{flow_id}` | Официальный endpoint |

---

**Статус:** Архитектурное решение утверждено. Документ готов для начала развёртывания.