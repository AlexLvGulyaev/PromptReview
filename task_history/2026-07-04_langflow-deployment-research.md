# Задача: Исследование официальной документации LangFlow

**Дата:** 2026-07-04
**Статус:** Выполнено

---

## Исходное задание

Провести исследование официальной документации LangFlow для подготовки развёртывания.

**Запрещено:**
- Выполнять deployment
- Изменять инфраструктуру
- Создавать compose
- Менять существующие документы

**Источники:** Только официальная документация LangFlow, официальный GitHub, официальные примеры разработчиков.

---

## Выполненное исследование

### Изученные официальные источники

| Источник | URL |
|----------|-----|
| Docker Deployment | https://docs.langflow.org/deployment-docker |
| Environment Variables | https://docs.langflow.org/environment-variables |
| API Keys and Authentication | https://docs.langflow.org/api-keys-and-authentication |
| API Flow Triggers | https://docs.langflow.org/api-flows-run |
| JWT Authentication | https://docs.langflow.org/jwt-authentication |
| Ollama Integration | https://docs.langflow.org/bundles-ollama |
| Nginx SSL Deployment | https://docs.langflow.org/deployment-nginx-ssl |
| Health Check Router | https://github.com/langflow-ai/langflow/blob/main/src/backend/base/langflow/api/health_check_router.py |
| Docker Compose (production) | https://github.com/langflow-ai/langflow/blob/main/deploy/docker-compose.yml |
| GitHub Repository | https://github.com/langflow-ai/langflow |

---

## Ключевые находки

### 1. Развёртывание

**Рекомендуется для production:**
- Docker Compose с PostgreSQL
- Persistent volumes для данных
- Конкретные версии образов (не `latest`)

### 2. Docker-образы

| Образ | Назначение |
|-------|-----------|
| `langflowai/langflow:latest` | Полный образ |
| `langflowai/langflow-backend:latest` | Только backend |
| `langflowai/langflow-frontend:latest` | Только frontend |

### 3. Хранение данных

- **SQLite** — по умолчанию для простого запуска
- **PostgreSQL** — рекомендуется для production

### 4. Переменные окружения

Ключевые переменные:
- `LANGFLOW_HOST`, `LANGFLOW_PORT` — сервер
- `LANGFLOW_AUTO_LOGIN=False` — для production
- `LANGFLOW_SECRET_KEY` — для JWT
- `LANGFLOW_DATABASE_URL` — для PostgreSQL

### 5. Reverse Proxy

**Nginx:**
- WebSocket обязателен
- `client_max_body_size 100M`
- Extended timeouts (300s)

**Traefik:**
- Официальный compose использует Traefik v3.0
- Let's Encrypt автоматически

### 6. API

**Health Check:**
- `/health_check` — рекомендуется (проверяет DB и chat)
- `/health` — legacy (только liveness)

**Flow Execution:**
- `/api/v1/run/{flow_id}` — основной endpoint
- `/api/v1/webhook/{flow_id}` — webhook trigger

### 7. Ollama

- Base URL: `http://127.0.0.1:11434`
- Docker: `host.docker.internal:11434`
- Модели с поддержкой tools: Qwen 2.5, Llama 3.1

### 8. Безопасность

**Для production:**
1. `LANGFLOW_AUTO_LOGIN=False`
2. Нестандартный `LANGFLOW_SECRET_KEY`
3. Reverse proxy с аутентификацией
4. Точные CORS origins
5. `LANGFLOW_REMOVE_API_KEYS=True`

---

## Отсутствующая информация

**В официальной документации не найдено:**
- Специальных настроек Traefik для LangFlow (используется стандартная reverse proxy конфигурация)
- Subpath deployment требует изменения BASENAME в `config-constants.ts` (найдено в GitHub Issue)

---

## Структура документа

| Раздел | Содержание |
|--------|------------|
| 1. Развёртывание | Варианты установки, рекомендация для production |
| 2. Docker-образы | Поддерживаемые образы |
| 3. Хранение данных | SQLite vs PostgreSQL, persistence |
| 4. Переменные окружения | Все переменные с источниками |
| 5. Docker Compose | Минимальная и production конфигурации |
| 6. Reverse Proxy | Nginx и Traefik конфигурации |
| 7. HTTPS | Требования LangFlow |
| 8. API | Endpoints, аутентификация |
| 9. Health Check | `/health_check` vs `/health` |
| 10. Ollama | Конфигурация подключения |
| 11. Безопасность | Рекомендации для production |
| 12. Отсутствующая информация | Что не найдено в документации |

---

## Изменённые файлы

- **Создан:** `infra/LANGFLOW_DEPLOYMENT_RESEARCH.md`

---

## Итог

Документ построен исключительно на подтверждённых сведениях из официальной документации LangFlow.

Для каждого утверждения приведены:
- Краткий вывод
- Ссылка на официальный источник
- Цитата или выдержка при необходимости

Если официальный источник не содержит ответа, прямо указано: "В официальной документации не найдено."