# LangFlow VPS Deployment Plan

План развёртывания LangFlow на VPS для кейса Prompt Review.

## 1. Цель развёртывания

LangFlow нужен как VPS-инстанс для:
- Воспроизведения Prompt Review Agent из PEl03
- Последующего вызова Flow внешними системами, в том числе n8n
- Предоставления визуального интерфейса для работы с AI Flow

## 2. Текущее состояние инфраструктуры

### Работающие контейнеры

| Контейнер | Образ | Назначение |
|-----------|-------|------------|
| `n8n-traefik-1` | traefik:v3.3 | Обратный прокси, SSL-терминация |
| `n8n-n8n-1` | n8nio/n8n | HR Assistant n8n |
| `n8n-postgres_hr-1` | postgres:16 | База HR Assistant |
| `lead-qualification-n8n` | n8nio/n8n:latest | Lead Qualification n8n |
| `lead-qualification-postgres` | postgres:16-alpine | База Lead Qualification |
| `lead-qualification-admin-backend` | infra_admin-backend | Admin API |
| `lead-qualification-admin-ui` | nginx:alpine | Admin UI |
| `lead-qualification-client-ui` | nginx:alpine | Client UI |
| `lead-qualification-landing` | nginx:alpine | Landing |

### Docker сети

| Сеть | Назначение |
|------|------------|
| `n8n_default` | Сеть Traefik для публикации сервисов |
| `lead-qualification-network` | Внутренняя сеть Lead Qualification |
| `prompt-engineering-lab_default` | Сеть PEL (postgres) |

### Traefik конфигурация

**Расположение:** `/opt/n8n/`
- `docker-compose.yml` — Traefik + HR Assistant n8n
- `dynamic.yml` — динамическая маршрутизация
- `acme.json` — SSL-сертификаты Let's Encrypt

**Публикация сервисов:**

| Маршрут | Сервис | Поддомен |
|---------|--------|----------|
| n8n-de.alex-n8n.site | HR Assistant n8n | `n8n-de` |
| lead-qual.alex-n8n.site/webhook | Lead Qualification n8n | `lead-qual` |
| lead-qual.alex-n8n.site | Client UI | `lead-qual` |
| lead-qual-admin.alex-n8n.site | Admin UI | `lead-qual-admin` |
| lead-qual-demo.alex-n8n.site | Landing | `lead-qual-demo` |

**Шаблон маршрутизации:**
```yaml
routers:
  service-name:
    rule: "Host(`subdomain.alex-n8n.site`)"
    entryPoints:
      - websecure
    tls:
      certResolver: myresolver
    service: service-name
```

### Ollama

**Статус:** Установлен на хосте (не в Docker)

**Доступ:** `http://localhost:11434`

**Модели:**
- `kimi-k2.7-code:cloud`
- `glm-5:cloud`

**Важно:** LangFlow в контейнере должен подключаться к Ollama через адрес хоста (`host.docker.internal:11434` или IP хоста).

### Важные ограничения

1. **Traefik управляется из `/opt/n8n/`** — любые изменения маршрутов требуют редактирования `/opt/n8n/dynamic.yml`
2. **Сеть `n8n_default`** — единственная сеть для публикации через Traefik
3. **Поддомены `*.alex-n8n.site`** — домен для всех публичных сервисов
4. **Ollama на хосте** — LangFlow должен подключаться к Ollama через host-адрес

## 3. Предлагаемая архитектура LangFlow

### Компоненты

```
LangFlow Container
├── LangFlow UI (порт 7860)
├── Flow Persistence (volume или PostgreSQL)
└── Connection: Ollama (host.docker.internal:11434)
```

### Сетевая архитектура

```
Internet
    ↓
Traefik (n8n_default)
    ↓
LangFlow Container (langflow-network + n8n_default)
    ↓
Ollama (host.docker.internal:11434)
```

### Persistence

**Вариант A: SQLite + Volume (рекомендуется для начала)**
- Простой в настройке
- Достаточно для Prompt Review Agent
- Volume: `langflow-data:/app/langflow`

**Вариант B: PostgreSQL (для production)**
- Отдельная база в существующем PostgreSQL
- Требует дополнительной настройки
- Рассмотреть при необходимости многопользовательской работы

### Безопасность

- Без аутентификации на первом этапе (внутренний доступ)
- HTTPS через Traefik
- Секреты через `.env` (не коммитировать)
- Изоляция через отдельную Docker-сеть

## 4. Файлы для создания на следующем шаге

| Файл | Назначение |
|------|------------|
| `infra/docker-compose.langflow.yml` | Docker Compose для LangFlow |
| `infra/.env.example` | Шаблон переменных окружения |
| `infra/.gitignore` | Исключение секретов |
| `/opt/n8n/dynamic.yml` | Добавление маршрута LangFlow |

### Docker Compose (предварительная структура)

```yaml
# Предварительная структура, не для выполнения
services:
  langflow:
    image: langflowai/langflow:latest
    container_name: prompt-review-langflow
    ports:
      - "7860:7860"
    volumes:
      - langflow-data:/app/langflow
    environment:
      - LANGFLOW_AUTO_LOGIN=true
      # Ollama connection
    networks:
      - langflow-network
      - n8n_default  # Для Traefik

networks:
  langflow-network:
    driver: bridge
  n8n_default:
    external: true

volumes:
  langflow-data:
```

### Traefik маршрут (предварительная структура)

```yaml
# Добавить в /opt/n8n/dynamic.yml
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

## 5. Риски

### Конфликт портов

**Риск:** Порт 7860 может быть занят.
**Митигация:** Проверить перед запуском: `netstat -tlnp | grep 7860`
**Альтернатива:** Использовать другой порт.

### Конфликт сетей

**Риск:** Некорректное подключение к `n8n_default`.
**Митигация:** Использовать `external: true` и явное имя сети.
**Проверка:** `docker network inspect n8n_default`

### Влияние на существующий n8n

**Риск:** LangFlow не влияет на n8n, но разделяет Traefik.
**Митигация:** LangFlow в изолированной сети + подключение к `n8n_default`.

### Хранение секретов

**Риск:** Секреты в `.env` могут быть случайно закоммичены.
**Митигация:** `.env` в `.gitignore`, использовать `.env.example`.

### Persistence данных LangFlow

**Риск:** Потеря Flow при перезапуске контейнера.
**Митигация:** Использовать Docker volume для `/app/langflow`.
**Бэкап:** Периодический экспорт Flow через LangFlow UI.

### Доступность Ollama

**Риск:** LangFlow в контейнере не может подключиться к Ollama на хосте.
**Решение:** Использовать `host.docker.internal:11434` (Linux) или IP хоста.
**Проверка:** `curl http://host.docker.internal:11434/api/tags` из контейнера.

### Публичный доступ к LangFlow

**Риск:** LangFlow без аутентификации доступен публично.
**Митигация:**
1. Ограничить доступ через Traefik middleware (IP whitelist)
2. Включить аутентификацию LangFlow
3. Использовать VPN/туннель для доступа

## 6. План реализации

### Шаг 1: Подготовка env-шаблона

- Создать `infra/.env.example` с переменными:
  - `LANGFLOW_HOST`
  - `LANGFLOW_PORT`
  - `LANGFLOW_AUTO_LOGIN`
- Создать `infra/.gitignore` для исключения `.env`

### Шаг 2: Создание compose

- Создать `infra/docker-compose.langflow.yml`
- Определить сервис LangFlow
- Настроить volume для persistence
- Подключить сети: `langflow-network` и `n8n_default`
- Настроить connection к Ollama

### Шаг 3: Подключение к Docker-сети

- Убедиться, что сеть `n8n_default` существует
- Проверить подключение: `docker network inspect n8n_default`

### Шаг 4: Настройка маршрута через Traefik

- Добавить маршрут в `/opt/n8n/dynamic.yml`
- Определить поддомен: `langflow.alex-n8n.site`
- Настроить TLS через Let's Encrypt

### Шаг 5: Запуск сервиса

- Создать `.env` из `.env.example`
- Запустить: `docker compose -f docker-compose.langflow.yml up -d`
- Проверить логи: `docker logs prompt-review-langflow`

### Шаг 6: Проверка health/status

- Проверить контейнер: `docker ps`
- Проверить здоровье: `curl http://localhost:7860/health`
- Проверить логи на ошибки

### Шаг 7: Открытие UI

- Дождаться SSL-сертификата Let's Encrypt
- Открыть `https://langflow.alex-n8n.site`
- Проверить доступность Ollama в настройках LangFlow

### Шаг 8: Создание/импорт Prompt Review Flow

- Воспроизвести Prompt Review Flow из PEl03
- Настроить модель: Ollama с gemma4:e4b
- Протестировать Flow в Playground

### Шаг 9: Проверка API Access

- Опубликовать Flow через API
- Скопировать API endpoint
- Протестировать вызов через curl

### Шаг 10: Интеграция с n8n

- В n8n создать HTTP Request node
- Настроить вызов LangFlow API
- Протестировать end-to-end сценарий

## 7. Критерии готовности

| Критерий | Проверка |
|----------|----------|
| Контейнер LangFlow работает | `docker ps \| grep langflow` |
| UI доступен по HTTPS | Открыть `https://langflow.alex-n8n.site` |
| Данные сохраняются после перезапуска | Перезапустить контейнер, проверить Flow |
| Flow можно создать/открыть | Создать тестовый Flow в UI |
| API Access доступен | Опубликовать Flow, вызвать через curl |
| n8n может вызвать Flow | HTTP Request node в n8n |

## Статус

План развёртывания. Развёртывание не выполнено. Инфраструктура не изменена.