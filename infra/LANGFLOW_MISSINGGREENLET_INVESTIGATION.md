# Инженерное расследование: MissingGreenlet в LangFlow 1.10.1 с PostgreSQL

**Дата:** 2026-07-04  
**Статус:** Завершено  
**Кейс:** prompt-review  

---

## 1. Описание симптома

### Наблюдаемая ошибка

LangFlow 1.10.1 успешно проходит health check и запускается, но при попытке работы с PostgreSQL возникает ошибка:

```
MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
Was IO attempted in an unexpected place?
```

### Стек ошибки

```
/app/.venv/lib/python3.14/site-packages/sqlalchemy/util/_concurrency_py3k.py:123
in await_only

app/.venv/lib/python3.14/site-packages/langflow/api/v1/mcp_projects.py:1573
in init_mcp_servers
```

### Контекст ошибки

Ошибка возникает при инициализации MCP серверов:
```
Failed to initialize MCP servers: greenlet_spawn has not been called
```

---

## 2. Фактическая конфигурация

### 2.1 Переменные окружения

```
LANGFLOW_DATABASE_URL=postgresql://langflow:***@postgres:5432/langflow
LANGFLOW_SECRET_KEY=t8u16yegRA8Oac8xnStmjlZCYQQsLcdx (32 символа)
LANGFLOW_AUTO_LOGIN=False
```

### 2.2 Версии в контейнере

| Компонент | Версия |
|-----------|--------|
| Python | 3.14.6 |
| LangFlow | 1.10.1 |
| SQLAlchemy | 2.0.51 |
| psycopg | 3.3.4 |
| psycopg2-binary | 2.9.12 |
| greenlet | 3.5.2 |
| alembic | 1.18.4 |

### 2.3 Драйверы PostgreSQL

Установлены оба драйвера:
- `psycopg` (v3, async) — используется LangFlow
- `psycopg2-binary` (v2, sync)

### 2.4 Трансформация URL

LangFlow автоматически трансформирует URL:

```
# Исходный (из .env):
postgresql://langflow:***@postgres:5432/langflow

# После _sanitize_database_url():
postgresql+psycopg://langflow:***@postgres:5432/langflow
```

### 2.5 Доступные диалекты PostgreSQL

```
psycopg      — async driver (используется)
psycopg2     — sync driver
asyncpg      — NOT SUPPORTED (LangFlow не поддерживает asyncpg)
```

---

## 3. Вторичная ошибка: Fernet Key

### Обнаруженная проблема

При анализе логов выявлена дополнительная ошибка:

```
ValueError: Fernet key must be 32 url-safe base64-encoded bytes.
```

### Причина

Функция `ensure_fernet_key` в LangFlow:

```python
MINIMUM_KEY_LENGTH = 32
if len(secret_key) < MINIMUM_KEY_LENGTH:
    # Ключи < 32 символов: SHA-256 хеш → base64
    digest = hashlib.sha256(secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
else:
    # Ключи >= 32 символов: предполагается, что это уже base64
    key = add_base64_padding(secret_key).encode()
```

### Проблема с текущим ключом

```
LANGFLOW_SECRET_KEY=t8u16yegRA8Oac8xnStmjlZCYQQsLcdx
```

- Длина: 32 символа
- Формат: случайный alphanumeric (НЕ base64)
- Результат: `ensure_fernet_key` возвращает `b't8u16yegRA8Oac8xnStmjlZCYQQsLcdx'`
- Fernet ожидает: 32 url-safe base64-encoded байта (44 символа в base64)

---

## 4. Версии зависимостей

### Python 3.14 — Experimental

LangFlow 1.10.1 работает на Python 3.14.6 (experimental):

| Версия Python | Статус |
|---------------|--------|
| 3.10–3.12 | Stable |
| 3.13 | Stable |
| **3.14** | **Experimental** |

### greenlet 3.5.2

- Версия: 3.5.2
- C-extension: доступен
- Совместимость с Python 3.14: ✅ (исправлено в greenlet 3.2+)

### SQLAlchemy 2.0.51

- asyncio extension: доступен
- greenlet dependency: установлен

---

## 5. Известные issues

### 5.1 Issue #5495: MissingGreenlet с MySQL/PostgreSQL async

**Статус:** Closed (исправлено в PR #6258)

**Исправление:** Использование `greenlet_spawn` вместо `asyncio.to_thread` для миграций.

**Важно:** Исправление касается миграций, но не runtime-кода.

### 5.2 Issue #10363: Psycopg3 на Windows

**Статус:** Closed (дубль #8247)

**Проблема:** `ProactorEventLoop` несовместим с async psycopg.

**Решение:** Для Windows — `WindowsSelectorEventLoopPolicy()`.

**Релевантность:** Linux использует `EpollSelectorEventLoop` — не должно затрагивать.

### 5.3 PR #10500: asyncpg не поддерживается

**Статус:** Merged

**Суть:** LangFlow НЕ поддерживает `asyncpg`, только `psycopg` или `psycopg2`.

### 5.4 PR #12595: Base64 padding bug

**Статус:** Merged

**Исправление:** Ошибка в `_add_padding` — добавлял 4 `=` вместо 0 при длине, кратной 4.

---

## 6. Анализ кода LangFlow

### 6.1 Инициализация MCP серверов

```python
# langflow/api/v1/mcp_projects.py:1573
async def init_mcp_servers():
    async with session_scope() as session:
        projects = (await session.exec(select(Folder))).all()
        for project in projects:
            # ... регистрация MCP сервера для каждого проекта
```

### 6.2 session_scope

```python
# langflow/services/deps.py
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    db_service = get_db_service()
    async with db_service._with_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
```

### 6.3 _with_session

```python
# langflow/services/database/service.py
async def _with_session(self):
    if self.settings_service.settings.use_noop_database:
        yield NoopSession()
    else:
        async with self.async_session_maker() as session:
            yield session
```

### 6.4 async_session_maker

```python
self.async_session_maker = async_sessionmaker(
    self.engine,
    class_=SQLModelAsyncSession,
    expire_on_commit=False,
)
```

---

## 7. Проверенные гипотезы

### Гипотеза 1: Некорректный Fernet Key (ПОДТВЕРЖДЕНА)

**Симптом:** `Fernet key must be 32 url-safe base64-encoded bytes`

**Причина:** `LANGFLOW_SECRET_KEY` — 32 символа alphanumeric, но не base64.

**Проверка:**
```python
from cryptography.fernet import Fernet
Fernet(b't8u16yegRA8Oac8xnStmjlZCYQQsLcdx')  # Ошибка!
```

**Статус:** ПОДТВЕРЖДЕНА. Это вторичная ошибка, но может влиять на общую стабильность.

---

### Гипотеза 2: Проблема с async context в MCP init (ВЫСОКАЯ ВЕРОЯТНОСТЬ)

**Симптом:** `MissingGreenlet` в `init_mcp_servers`

**Анализ:**
1. MCP init выполняется через `asyncio.create_task(delayed_init_mcp_servers())`
2. Внутри вызывается `session_scope()` → `_with_session()` → `async_session_maker()`
3. При обращении к `Folder` возникает `MissingGreenlet`

**Возможные причины:**
- SQLAlchemy async engine требует greenlet context
- `session.exec(select(Folder))` пытается выполнить IO без greenlet_spawn
- Python 3.14 может иметь особенности в async/greenlet взаимодействии

**Статус:** Требует дополнительного расследования.

---

### Гипотеза 3: Python 3.14 + greenlet несовместимость (СРЕДНЯЯ ВЕРОЯТНОСТЬ)

**Факты:**
- Python 3.14 — experimental
- greenlet 3.5.2 — последняя версия
- SQLAlchemy 2.0.51 официально поддерживает Python 3.14

**Проверка:**
```python
import greenlet
greenlet.__version__  # '3.5.2' ✅
greenlet._C_API       # <capsule object> ✅
```

**Статус:** Маловероятно, но возможно edge case.

---

## 8. Вывод о наиболее вероятной причине

### Первичная причина

**Некорректный `LANGFLOW_SECRET_KEY`** вызывает ошибку Fernet при попытке шифрования API ключей MCP.

### Вторичная причина (вероятная)

Ошибка Fernet прерывает нормальный flow инициализации MCP, что приводит к некорректному состоянию сессии и последующему `MissingGreenlet`.

### Корневая проблема

Функция `ensure_fernet_key` в LangFlow некорректно обрабатывает ключи длиной >= 32 символа, если они не являются base64.

---

## 9. Безопасный план исправления

### Шаг 1: Исправить LANGFLOW_SECRET_KEY

**Текущий (некорректный):**
```
LANGFLOW_SECRET_KEY=t8u16yegRA8Oac8xnStmjlZCYQQsLcdx
```

**Корректный (Fernet-generated):**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Пример: u7ZxK9mN2pQrS5vW8yB1cD4fG6hJ3kL0mN5oP8qR1sU=
```

### Шаг 2: Обновить .env

```bash
# infra/.env
LANGFLOW_SECRET_KEY=<новый_fernet_ключ>
```

### Шаг 3: Перезапустить контейнер

```bash
docker compose -f docker-compose.langflow.yml restart langflow
```

### Шаг 4: Проверить логи

```bash
docker logs prompt-review-langflow -f
```

### Критерии успеха

- ✅ Отсутствие ошибки `Fernet key must be 32 url-safe base64-encoded bytes`
- ✅ Успешная инициализация MCP серверов
- ✅ Отсутствие `MissingGreenlet` ошибок
- ✅ Health check: `{"status":"ok","chat":"ok","db":"ok"}`

---

## 10. Источники

- [Issue #5495 — MissingGreenlet с MySQL](https://github.com/langflow-ai/langflow/issues/5495)
- [PR #6258 — Use Alembic with async driver](https://github.com/langflow-ai/langflow/pull/6258)
- [PR #10500 — asyncpg не поддерживается](https://github.com/langflow-ai/langflow/pull/10500)
- [PR #12595 — Base64 padding bug fix](https://github.com/langflow-ai/langflow/pull/12595)
- [Issue #5598 — Fernet key error](https://github.com/langflow-ai/langflow/issues/5598)
- [Issue #10363 — Psycopg3 на Windows](https://github.com/langflow-ai/langflow/issues/10363)
- [SQLAlchemy AsyncIO Documentation](https://www.sqlalchemy.org/docs/orm/extensions/asyncio.html)
- [SQLAlchemy Discussion #12140 — MissingGreenlet errors](https://github.com/sqlalchemy/sqlalchemy/discussions/12140)
- [SQLAlchemy Issue #10088 — MissingGreenlet error](https://github.com/sqlalchemy/sqlalchemy/issues/10088)

---

---

## 12. Экспериментальная проверка

**Дата:** 2026-07-04  
**Статус:** ЗАВЕРШЕНО

### Исходное состояние

```
LANGFLOW_SECRET_KEY=t8u16yegRA8Oac8xnStmjlZCYQQsLcdx
```

- Длина: 32 символа
- Формат: alphanumeric (НЕ base64)
- Ошибки: `Fernet key must be 32 url-safe base64-encoded bytes` + `MissingGreenlet`

### Действие

**Шаг 1:** Генерация корректного Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Результат: rzOCc6dhqizluNUTXN_DyjmNO-GV21TJ7uvsG-0drOA=
```

**Шаг 2:** Обновление `infra/.env`:

```
LANGFLOW_SECRET_KEY=rzOCc6dhqizluNUTXN_DyjmNO-GV21TJ7uvsG-0drOA=
```

**Шаг 3:** Пересоздание контейнера:

```bash
docker compose -f docker-compose.langflow.yml up -d langflow
```

### Результаты проверки

| Проверка | До | После |
|----------|-----|-------|
| Fernet key ошибка | ❌ Присутствует | ✅ Отсутствует |
| MissingGreenlet ошибка | ❌ Присутствует | ✅ Отсутствует |
| Health check | ✅ `{"status":"ok"}` | ✅ `{"status":"ok"}` |
| MCP инициализация | ❌ Ошибка | ✅ Успешно |
| Логи запуска | Ошибки Fernet + Greenlet | Только CORS warnings |

**Логи после исправления:**

```
✓ Connecting Database
✓ Loading Components
✓ Adding Starter Projects
✓ Launching Langflow

[info] Auto-enabled API key authentication for existing project Starter Project
[info] File _mcp_servers_50aa8c95-319e-4527-99a1-44ead4332ab3.json saved successfully
```

**Подсчёт ошибок:**

```bash
docker logs prompt-review-langflow 2>&1 | grep -c "MissingGreenlet"
# 0

docker logs prompt-review-langflow 2>&1 | grep -c "Fernet key must be"
# 0
```

### Вывод эксперимента

**Корневая причина установлена:** Некорректный `LANGFLOW_SECRET_KEY`.

**Механизм:**
1. `LANGFLOW_SECRET_KEY` = 32 символа alphanumeric
2. `ensure_fernet_key()` предполагает, что ключи >= 32 символа уже base64
3. Функция возвращает некорректный Fernet key
4. Попытка шифрования API ключей MCP вызывает `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`
5. Ошибка прерывает инициализацию MCP в середине async context
6. SQLAlchemy async session оказывается в некорректном состоянии
7. При следующей попытке IO возникает `MissingGreenlet`

**Статус гипотез:**

| Гипотеза | Результат |
|----------|-----------|
| Fernet Key — корневая причина | ✅ **ПОДТВЕРЖДЕНА** |
| Проблема async context в MCP init | ❌ Отвергнута (исчезло после исправления Fernet) |
| Python 3.14 + greenlet несовместимость | ❌ Отвергнута (исчезло после исправления Fernet) |

---

## 13. Финальные рекомендации

### Для текущего deployment

✅ Исправление применено. LangFlow работает корректно.

### Для будущих deployments

**Требование к `LANGFLOW_SECRET_KEY`:**

```bash
# Правильный способ генерации:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Результат: 44 символа base64 (32 байта при декодировании)
# Пример: u7ZxK9mN2pQrS5vW8yB1cD4fG6hJ3kL0mN5oP8qR1sU=
```

**Неправильно:**
```
# 32 символа alphanumeric — НЕ Fernet key
LANGFLOW_SECRET_KEY=t8u16yegRA8Oac8xnStmjlZCYQQsLcdx
```

**Правильно:**
```
# 44 символа base64 — корректный Fernet key
LANGFLOW_SECRET_KEY=rzOCc6dhqizluNUTXN_DyjmNO-GV21TJ7uvsG-0drOA=
```

---

## 14. Изменённые файлы

- **Обновлён:** `infra/.env` — `LANGFLOW_SECRET_KEY` заменён на корректный Fernet key