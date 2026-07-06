# LangFlow Deployment Research

Исследование официальной документации LangFlow для подготовки развёртывания.

**Источники:** Только официальная документация LangFlow и официальный GitHub-репозиторий.

---

## 1. Официально рекомендуемый способ развёртывания

### Варианты установки

| Метод | Описание | Источник |
|------|----------|----------|
| **LangFlow Desktop** | Готовое приложение для Windows/macOS | [langflow.org/desktop](https://www.langflow.org/desktop) |
| **Python Package** | `pip install langflow` или `uv pip install langflow -U` | [docs.langflow.org/get-started-installation](https://docs.langflow.org/get-started-installation) |
| **Docker** | `docker run -p 7860:7860 langflowai/langflow:latest` | [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker) |
| **Docker Compose** | Рекомендуется для production | [github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml) |

### Рекомендация для production

> "For more control with persistent PostgreSQL database: Clone the repository and use Docker Compose."

**Источник:** [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker)

---

## 2. Поддерживаемые Docker-образы

| Образ | Назначение | Источник |
|-------|-----------|----------|
| `langflowai/langflow:latest` | Последняя версия | [Docker Hub](https://hub.docker.com/r/langflowai/langflow) |
| `langflowai/langflow:1.8.0` | Конкретная версия | Пример из документации |
| `langflowai/langflow-backend:latest` | Только backend | [GitHub docker-compose.yml](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml) |
| `langflowai/langflow-frontend:latest` | Только frontend | [GitHub docker-compose.yml](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml) |

**Рекомендация по версиям:**

> "Pin specific image versions (e.g., `1.8.0`) for controlled upgrades."

**Источник:** [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker)

---

## 3. Способы хранения данных

### SQLite

**Статус:** База данных по умолчанию при использовании быстрого запуска.

> "SQLite is the default database when using the quickstart Docker command."

**Источник:** [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker)

### PostgreSQL

**Статус:** Рекомендуется для production.

> "When cloning the repo and using Docker Compose, the default deployment uses PostgreSQL instead of the default SQLite database."

**Формат подключения:**

```
LANGFLOW_DATABASE_URL=postgresql://user:password@host:5432/langflow
```

**Источник:** [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker)

### Persistence

**Рекомендация:**

> "Use persistent volumes to ensure data survives container restarts. Keep data on persistent volumes, so when you upgrade Langflow, you will replace only the container image."

**Источник:** [docs.langflow.org/deployment-docker](https://docs.langflow.org/deployment-docker)

---

## 4. Переменные окружения

### Категории переменных

| Категория | Переменные |
|-----------|------------|
| Server Configuration | `LANGFLOW_HOST`, `LANGFLOW_PORT`, `LANGFLOW_BACKEND_ONLY`, `LANGFLOW_WORKERS`, `LANGFLOW_WORKER_TIMEOUT` |
| Database | `LANGFLOW_DATABASE_URL`, `LANGFLOW_SAVE_DB_IN_CONFIG_DIR` |
| Security | `LANGFLOW_AUTO_LOGIN`, `LANGFLOW_SECRET_KEY`, `LANGFLOW_SUPERUSER`, `LANGFLOW_SUPERUSER_PASSWORD` |
| API | `LANGFLOW_API_KEY_SOURCE`, `LANGFLOW_REMOVE_API_KEYS` |
| SSL | `LANGFLOW_SSL_CERT_FILE`, `LANGFLOW_SSL_KEY_FILE` |

### Ключевые переменные

| Переменная | По умолчанию | Описание | Обязательная |
|-----------|--------------|----------|--------------|
| `LANGFLOW_HOST` | `localhost` | Хост сервера | Нет |
| `LANGFLOW_PORT` | `7860` | Порт сервера | Нет |
| `LANGFLOW_AUTO_LOGIN` | `False` | Автоматический вход (для production установить `False`) | Нет |
| `LANGFLOW_SECRET_KEY` | Auto-generated | Секретный ключ для HS256 JWT | Для production |
| `LANGFLOW_DATABASE_URL` | SQLite | URL подключения к PostgreSQL | Для PostgreSQL |
| `LANGFLOW_SUPERUSER` | — | Имя суперпользователя | Нет |
| `LANGFLOW_SUPERUSER_PASSWORD` | — | Пароль суперпользователя | Нет |

**Источник:** [docs.langflow.org/environment-variables](https://docs.langflow.org/environment-variables)

---

## 5. Официальная структура Docker Compose

### Минимальная конфигурация

```yaml
services:
  langflow:
    image: langflowai/langflow:latest
    ports:
      - "7860:7860"
    volumes:
      - langflow-data:/app/langflow

volumes:
  langflow-data:
```

### Production конфигурация

Официальный docker-compose.yml включает:

| Сервис | Назначение | Образ |
|--------|-----------|-------|
| `proxy` | Traefik v3.0 reverse proxy | `traefik:v3.0` |
| `backend` | LangFlow API | `langflowai/langflow-backend:latest` |
| `frontend` | LangFlow UI | `langflowai/langflow-frontend:latest` |
| `db` | PostgreSQL 15.4 | `postgres:15.4` |
| `broker` | RabbitMQ | `rabbitmq:3-management` |
| `result_backend` | Redis | `redis:6.2.5` |
| `celeryworker` | Background tasks | `langflowai/langflow-backend:latest` |
| `flower` | Celery monitoring | `langflowai/langflow-backend:latest` |
| `prometheus` | Metrics | `prom/prometheus:v2.37.9` |
| `grafana` | Dashboard | `grafana/grafana:8.2.6` |

**Источник:** [github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml)

### Обязательные параметры

Для production deployment с официальным compose требуются переменные:

- `TRAEFIK_PUBLIC_NETWORK`
- `TRAEFIK_TAG`
- `TRAEFIK_PUBLIC_TAG`
- `STACK_NAME`
- `DOMAIN`
- `BROKER_URL`

---

## 6. Работа за reverse proxy

### Nginx

**Официальная документация:** [docs.langflow.org/deployment-nginx-ssl](https://docs.langflow.org/deployment-nginx-ssl)

**Ключевые настройки:**

```nginx
server {
    listen 80;
    server_name DOMAIN_NAME;
    
    client_max_body_size 100M;  # Для загрузки файлов
    
    location / {
        proxy_pass http://127.0.0.1:7860/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts для long-running flows
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

**Особенности:**
- WebSocket обязателен для real-time features
- `client_max_body_size` для загрузки файлов
- Extended timeouts для долгих flows

### Traefik

**Официальный compose использует Traefik v3.0 с:**

- HTTPS redirection через middlewares
- Let's Encrypt SSL certificates (автоматические)
- Path-based routing для разных сервисов

**Маршрутизация:**

```yaml
# Backend API
traefik.http.routers.backend-http.rule=PathPrefix(`/api/v1`) || PathPrefix(`/api/v2`) || PathPrefix(`/docs`) || PathPrefix(`/health`)

# Frontend
traefik.http.routers.frontend-http.rule=PathPrefix(`/`)
```

**Источник:** [github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml)

---

## 7. HTTPS

### Требования LangFlow

**В официальной документации не найдено специальных требований LangFlow к HTTPS.**

HTTPS полностью остаётся задачей reverse proxy (Nginx, Traefik).

### Переменные SSL

| Переменная | Описание |
|-----------|----------|
| `LANGFLOW_SSL_CERT_FILE` | Путь к SSL-сертификату |
| `LANGFLOW_SSL_KEY_FILE` | Путь к SSL-ключу |

**Примечание:** Эти переменные указаны в документации, но для production рекомендуется использовать reverse proxy с Let's Encrypt.

---

## 8. API

### Аутентификация

**Типы аутентификации:**

1. **LangFlow API Keys** — основной метод
2. **Component API Keys** — для внешних сервисов
3. **Environment variable validation** — через `LANGFLOW_API_KEY_SOURCE=env`

**Источник:** [docs.langflow.org/api-keys-and-authentication](https://docs.langflow.org/api-keys-and-authentication)

### Создание API Key

**Через UI:**
1. Profile icon → Settings
2. Langflow API Keys → Add New
3. Name key → Create API Key

**Через CLI:**
```bash
langflow api-key
```
(Требуется для `--backend-only` режима)

### Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/v1/run/{flow_id}` | POST | Выполнение flow |
| `/api/v1/webhook/{flow_id}` | POST | Webhook trigger |
| `/api/v1/login` | POST | JWT login |
| `/api/v1/refresh` | POST | JWT refresh |
| `/health_check` | GET | Health check (recommended) |
| `/health` | GET | Liveness (legacy) |
| `/api/v1/version` | GET | Version info |

**Источник:** [docs.langflow.org/api-flows-run](https://docs.langflow.org/api-flows-run)

### Выполнение Flow

**Пример запроса:**

```bash
curl -X POST \
  "http://$LANGFLOW_SERVER/api/v1/run/$FLOW_ID?stream=false" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d '{"input_value": "hello", "input_type": "chat", "output_type": "chat"}'
```

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `flow_id` | UUID | ID flow (в URL) |
| `stream` | Boolean | Streaming mode |
| `input_value` | string | Входной текст |
| `input_type` | string | "chat" или "text" |
| `output_type` | string | "chat", "any", "debug" |
| `session_id` | string | ID сессии |
| `tweaks` | object | Настройки компонентов |

---

## 9. Health Check

### `/health_check` (Рекомендуется)

**Endpoint:** `GET /health_check`

**Что проверяет:**
- Database connectivity
- Chat service cache operations

**Response:**

```json
{
  "status": "ok",
  "chat": "ok",
  "db": "ok"
}
```

**Status codes:**
- `200 OK` — все сервисы здоровы
- `500 Internal Server Error` — один или более сервисов недоступны

**Источник:** [github.com/langflow-ai/langflow/blob/main/src/backend/base/langflow/api/health_check_router.py](https://github.com/langflow-ai/langflow/blob/main/src/backend/base/langflow/api/health_check_router.py)

### `/health` (Legacy)

**Предупреждение:**

> "This endpoint is served by uvicorn before LangFlow is fully initialized, so it can return 200 OK even when LangFlow services are not ready. Use `/health_check` for deployment readiness probes."

**Источник:** [github.com/langflow-ai/langflow/issues/8921](https://github.com/langflow-ai/langflow/issues/8921)

### Рекомендация для Kubernetes/Docker

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 7860

readinessProbe:
  httpGet:
    path: /health_check
    port: 7860
```

---

## 10. Работа с Ollama

### Конфигурация подключения

**Параметры:**

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| Base URL | `http://127.0.0.1:11434` | Адрес Ollama сервера |
| Model Name | — | Выбор модели |
| Temperature | `0.1` | Случайность (0.0-1.0) |
| Stream | `false` | Потоковая передача |

**Источник:** [docs.langflow.org/bundles-ollama](https://docs.langflow.org/bundles-ollama)

### Docker-конфигурация

**При запуске LangFlow в контейнере, а Ollama на хосте:**

> "Use `http://host.docker.internal:11434` (Docker Desktop) or use `http://<host-ip>:11434` from the container."

**Источник:** [docs.langflow.org/bundles-ollama](https://docs.langflow.org/bundles-ollama)

### Модели с поддержкой tools

**Рекомендация:**

> "Use models that support tools (e.g., Qwen 2.5, Llama 3.1). Enable the 'Tool Model Enabled' radio button in LangFlow."

**Проблема с обнаружением моделей:**

> "Ensure Ollama is running locally before opening LangFlow. Use `http://127.0.0.1:11434` or `http://localhost:11434` (avoid `http://0.0.0.0:11434`)."

---

## 11. Безопасность

### Аутентификация

**Переменные:**

| Переменная | По умолчанию | Описание |
|-----------|--------------|----------|
| `LANGFLOW_AUTO_LOGIN` | `False` | Автоматический вход |
| `LANGFLOW_SUPERUSER` | — | Имя суперпользователя |
| `LANGFLOW_SUPERUSER_PASSWORD` | — | Пароль суперпользователя |
| `LANGFLOW_SECRET_KEY` | Auto-generated | Секретный ключ JWT |
| `LANGFLOW_ENABLE_SUPERUSER_CLI` | — | CLI создание суперпользователя |

### Рекомендации для production

1. **Никогда не открывать порты LangFlow напрямую в интернет**

2. **Установить `LANGFLOW_AUTO_LOGIN=False`**

3. **Использовать нестандартный `LANGFLOW_SECRET_KEY`**

4. **Разместить за reverse proxy с аутентификацией**

5. **Установить `LANGFLOW_ENABLE_SUPERUSER_CLI=False`**

6. **Указать точные CORS origins:**

```env
LANGFLOW_CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

7. **Установить `LANGFLOW_REMOVE_API_KEYS=True`** для исключения API keys из сохранённых flow

8. **Регулярно ротировать `LANGFLOW_SECRET_KEY`**

**Источник:** [docs.langflow.org/api-keys-and-authentication](https://docs.langflow.org/api-keys-and-authentication)

### JWT Authentication

**Поддерживаемые алгоритмы:**

| Алгоритм | Описание |
|----------|----------|
| `HS256` | Симметричный, по умолчанию |
| `RS256` | Асимметричный, RSA private/public key |
| `RS512` | RSA с SHA-512 |

**Переменные:**

| Переменная | По умолчанию | Описание |
|-----------|--------------|----------|
| `LANGFLOW_ALGORITHM` | `HS256` | Алгоритм подписи |
| `LANGFLOW_ACCESS_TOKEN_EXPIRE_SECONDS` | `3600` | Время жизни access token |
| `LANGFLOW_REFRESH_TOKEN_EXPIRE_SECONDS` | `604800` | Время жизни refresh token |

**Источник:** [docs.langflow.org/jwt-authentication](https://docs.langflow.org/jwt-authentication)

---

## 12. Отсутствующая информация

### Traefik-специфичные рекомендации

**В официальной документации не найдено:**
- Специальных настроек Traefik для LangFlow (используется стандартная конфигурация reverse proxy)

### Subpath deployment

**Проблема:** White screen при развёртывании на subpath (например, `/langflow`)

**Решение (GitHub Issue):**

> "You need to set the BASENAME in `config-constants.ts` to match your subpath."

**Источник:** [github.com/langflow-ai/langflow/issues/9762](https://github.com/langflow-ai/langflow/issues/9762)

---

## Источники

1. [LangFlow Docker Deployment](https://docs.langflow.org/deployment-docker)
2. [LangFlow Environment Variables](https://docs.langflow.org/environment-variables)
3. [LangFlow API Keys and Authentication](https://docs.langflow.org/api-keys-and-authentication)
4. [LangFlow API Flow Triggers](https://docs.langflow.org/api-flows-run)
5. [LangFlow JWT Authentication](https://docs.langflow.org/jwt-authentication)
6. [LangFlow Ollama Integration](https://docs.langflow.org/bundles-ollama)
7. [LangFlow Deployment with Nginx SSL](https://docs.langflow.org/deployment-nginx-ssl)
8. [LangFlow Health Check Router](https://github.com/langflow-ai/langflow/blob/main/src/backend/base/langflow/api/health_check_router.py)
9. [LangFlow Docker Compose](https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml)
10. [LangFlow GitHub Repository](https://github.com/langflow-ai/langflow)

---

**Статус:** Исследование завершено. Все сведения подтверждены официальной документацией LangFlow.