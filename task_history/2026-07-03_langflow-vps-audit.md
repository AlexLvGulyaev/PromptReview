# Задача: Аудит и план развёртывания LangFlow на VPS

**Дата:** 2026-07-03
**Статус:** Выполнено

---

## Исходное задание

Подготовить аудит и план развёртывания LangFlow на VPS без выполнения deployment.

**Запрещено:**
- Изменять Docker, docker-compose, Traefik, dynamic.yml
- Создавать контейнеры, перезапускать сервисы
- Создавать .env, домены, менять DNS
- Выполнять deployment

---

## Результаты аудита

### Обнаруженная инфраструктура

**Работающие контейнеры:**
- `n8n-traefik-1` — Traefik v3.3 (обратный прокси, SSL)
- `n8n-n8n-1` — HR Assistant n8n
- `n8n-postgres_hr-1` — PostgreSQL для HR Assistant
- `lead-qualification-n8n` — Lead Qualification n8n
- `lead-qualification-postgres` — PostgreSQL для Lead Qualification
- `lead-qualification-admin-backend` — Admin API
- `lead-qualification-admin-ui` — Admin UI (nginx)
- `lead-qualification-client-ui` — Client UI (nginx)
- `lead-qualification-landing` — Landing (nginx)
- `pel-postgres` — PostgreSQL для Prompt Engineering Lab
- `portfolio-test-*` — контейнеры portfolio проекта
- `review-flow-*` — контейнеры review-flow проекта

**Docker сети:**
- `n8n_default` — сеть Traefik для публикации сервисов
- `lead-qualification-network` — внутренняя сеть Lead Qualification
- `prompt-engineering-lab_default` — сеть PEL
- `portfolio-test_default` — сеть portfolio
- `review-flow_default` — сеть review-flow

**Traefik конфигурация:**
- Расположение: `/opt/n8n/`
- Docker Compose: `/opt/n8n/docker-compose.yml`
- Dynamic config: `/opt/n8n/dynamic.yml`
- SSL сертификаты: `/opt/n8n/acme.json`

**Публикация сервисов:**
- Домен: `*.alex-n8n.site`
- Let's Encrypt через ACME HTTP challenge
- Маршруты в dynamic.yml через Host rules

**Ollama:**
- Установлен на хосте (не в Docker)
- Адрес: `http://localhost:11434`
- Модели: `kimi-k2.7-code:cloud`, `glm-5:cloud`

### Шаблон развёртывания сервисов

Изучен кейс `n8n-lead-qualification`:

1. Docker Compose в `infra/docker-compose.yml`
2. `.env.example` в `infra/`
3. Отдельная сеть проекта + подключение к `n8n_default`
4. Маршрут в `/opt/n8n/dynamic.yml`
5. Поддомен `*.alex-n8n.site`

---

## Предложенная архитектура

### Компоненты LangFlow

- Docker контейнер: `langflowai/langflow:latest`
- Порт: 7860
- Persistence: Docker volume `langflow-data`
- Сети: `langflow-network` (внутренняя) + `n8n_default` (Traefik)
- Поддомен: `langflow.alex-n8n.site`

### Подключение к Ollama

LangFlow в контейнере подключается к Ollama на хосте через:
- `host.docker.internal:11434` (Linux)
- Или IP-адрес хоста

### Безопасность

- HTTPS через существующий Traefik + Let's Encrypt
- Без аутентификации на первом этапе (внутренний доступ)
- Секреты через `.env` (исключён из git)

---

## Найденные риски

| Риск | Митигация |
|------|-----------|
| Конфликт портов | Проверить `netstat -tlnp \| grep 7860` |
| Конфликт сетей | Использовать `external: true` для `n8n_default` |
| Доступность Ollama | `host.docker.internal:11434` из контейнера |
| Persistence | Docker volume для `/app/langflow` |
| Публичный доступ | IP whitelist или аутентификация |
| Секреты в git | `.env` в `.gitignore` |

---

## Планируемые файлы

| Файл | Назначение |
|------|------------|
| `infra/docker-compose.langflow.yml` | Docker Compose для LangFlow |
| `infra/.env.example` | Шаблон переменных |
| `infra/.gitignore` | Исключение секретов |
| `/opt/n8n/dynamic.yml` | Добавление маршрута |

---

## Фиксация

**Инфраструктура не изменена.**

Выполнен только аудит:
- Изучены работающие контейнеры
- Изучены Docker сети
- Изучена конфигурация Traefik
- Изучен шаблон развёртывания из `n8n-lead-qualification`
- Проверен статус Ollama

Создан план развёртывания без выполнения deployment.

---

## Изменённые файлы

- **Создан:** `infra/LANGFLOW_VPS_DEPLOYMENT_PLAN.md`