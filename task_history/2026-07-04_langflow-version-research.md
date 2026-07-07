# Задача: Исследование MissingGreenlet и рекомендуемой версии LangFlow

**Дата:** 2026-07-04
**Статус:** Выполнено

---

## Исходное задание

Определить, является ли MissingGreenlet известной проблемой текущей версии LangFlow / SQLAlchemy / Python 3.14, используя исключительно GitHub Issues LangFlow и официальную документацию.

Если проблема известна — определить рекомендуемую стабильную версию образа вместо `latest`.

---

## Результаты исследования

### 1. MissingGreenlet — известная проблема

**GitHub Issue:** [#5495](https://github.com/langflow-ai/langflow/issues/5495)

**Статус:** Закрыта (resolved)

**Таймлайн:**
| Дата | Событие |
|------|---------|
| 31 декабря 2024 | Issue открыт (версия 1.1.1) |
| 11 февраля 2025 | PR #6258 влит в `main` |

**Корневая причина:**
SQLAlchemy async engine требует greenlet context для выполнения синхронных операций. LangFlow вызывал синхронные миграции через `asyncio.to_thread()`, что несовместимо с async драйверами SQLAlchemy.

**Решение:**
PR #6258 "feat: Use Alembic with async driver" реализовал поддержку async driver по [официальной документации Alembic](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic).

**Затронутые версии:**
- Версии до 1.1.x (декабрь 2024) содержат баг
- Версии после 11 февраля 2025 содержат фикс

**Вывод:** Проблема известна и исправлена. Все версии, выпущенные после 11 февраля 2025, содержат фикс.

---

### 2. Версии LangFlow

**Текущий выпуск:** v1.10.1 (23 июня 2025)

**Хронология релизов:**

| Версия | Дата | Примечание |
|--------|------|------------|
| 1.10.1 | 23 июня 2025 | Latest stable, security fixes |
| 1.10.0 | 9 июня 2025 | Major release |
| 1.9.6 | 2 июня 2025 | Bug fixes |
| 1.9.3 | 15 мая 2025 | **Critical security release** |
| 1.3.0 | 31 марта 2025 | MCP Client/Server, Launch Week |
| 1.2.0+ | после 11 февраля 2025 | Содержит фикс MissingGreenlet |
| 1.1.x | декабрь 2024 | Содержит баг MissingGreenlet |

---

### 3. Поддержка Python

**Текущие требования:** `requires-python = ">=3.10,<3.15"`

| Версия Python | Статус |
|---------------|--------|
| 3.10, 3.11, 3.12 | Stable — полностью поддерживаются |
| 3.13 | Stable — недавно переведён из experimental |
| 3.14 | Experimental — добавлена поддержка, но не все зависимости совместимы |

**Проблемы Python 3.14:**
- `ast.Num` удалён — заменён на `ast.Constant`
- Некоторые пакеты не имеют wheels для 3.14 (faiss-cpu, onnxruntime, langchain-ibm и др.)
- Docker-образы LangFlow используют Python 3.14, но это experimental

**Commit:** [a80cf1c](https://github.com/langflow-ai/langflow/commit/a80cf1c6496d5323e8e2e795cccb0a6e9414081d) — добавлена поддержка Python 3.14

**PR #13772:** Python 3.13 переведён в stable CI, Python 3.14 добавлен как experimental

---

### 4. Рекомендуемая версия Docker-образа

**Официальная рекомендация из документации:**

> Pin to specific versions for production stability. Use `langflowai/langflow:1.8.0` instead of `:latest`.

**Доступные стабильные теги:**

| Тег | Описание |
|-----|----------|
| `langflowai/langflow:latest` | Последний стабильный релиз (1.10.1) |
| `langflowai/langflow:1.10.1` | Latest stable (июнь 2025) |
| `langflowai/langflow:1.9.6` | Предыдущий stable (июнь 2025) |
| `langflowai/langflow:1.8.0` | Старый stable (документация рекомендует для примера) |

**Рекомендация для production:**

```yaml
image: langflowai/langflow:1.10.1
```

**Обоснование:**
1. Содержит фикс MissingGreenlet (влит 11 февраля 2025)
2. Содержит критические security fixes (1.9.3+)
3. Проверенный стабильный релиз
4. Предсказуемые обновления и возможность отката

---

### 5. Дополнительные рекомендации по PostgreSQL

**Windows Event Loop Issue (Issue #5983):**
При использовании `LANGFLOW_DATABASE_URL` с PostgreSQL на Windows требуется:

```python
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

**Для Linux VPS:** Не требуется, используется стандартный epoll event loop.

---

## Выводы

| Вопрос | Ответ |
|--------|-------|
| MissingGreenlet — известная проблема? | Да, Issue #5495, исправлена в PR #6258 |
| В каких версиях исправлена? | Все версии после 11 февраля 2025 (1.2.0+) |
| Python 3.14 — stable? | Нет, experimental. Не все зависимости совместимы |
| Рекомендуемый Docker-образ | `langflowai/langflow:1.10.1` (pinned) |
| Использовать `:latest` в production? | Не рекомендуется — использовать pinned version |

---

## Источники

- [Issue #5495 — MissingGreenlet error](https://github.com/langflow-ai/langflow/issues/5495)
- [PR #6258 — Use Alembic with async driver](https://github.com/langflow-ai/langflow/pull/6258)
- [PR #4408 — AsyncSession support](https://github.com/langflow-ai/langflow/pull/4408)
- [Commit a80cf1c — Python 3.14 support](https://github.com/langflow-ai/langflow/commit/a80cf1c6496d5323e8e2e795cccb0a6e9414081d)
- [PR #13772 — Python 3.13 stable, 3.14 experimental](https://github.com/langflow-ai/langflow/pull/13772)
- [LangFlow Releases](https://github.com/langflow-ai/langflow/releases)
- [LangFlow Release Notes](https://docs.langflow.org/release-notes)
- [LangFlow Docker Deployment](https://docs.langflow.org/deployment-docker)
- [Issue #5983 — Windows PostgreSQL async](https://github.com/langflow-ai/langflow/issues/5983)

---

## Применение изменений

**Действие:** Обновление docker-compose.langflow.yml с pinned версией.

### Изменение

```yaml
# Было:
image: langflowai/langflow:latest

# Стало:
# Pinned version: Contains MissingGreenlet fix (PR #6258) + security fixes
# Research: task-history/2026-07-04_langflow-version-research.md
image: langflowai/langflow:1.10.1
```

### Выполненные команды

```bash
# Pull нового образа
docker pull langflowai/langflow:1.10.1

# Пересоздание контейнера
docker compose -f docker-compose.langflow.yml up -d langflow
```

### Результат

| Компонент | Образ | Статус |
|-----------|-------|--------|
| `prompt-review-langflow` | `langflowai/langflow:1.10.1` | healthy ✅ |
| `prompt-review-postgres` | `postgres:16-alpine` | healthy ✅ |

**Health check:**
```json
{"status":"ok","chat":"ok","db":"ok"}
```

**URL:** https://langflow.alex-n8n.site

---

## Изменённые файлы

- **Обновлён:** `infra/docker-compose.langflow.yml` — версия `:latest` → `:1.10.1`