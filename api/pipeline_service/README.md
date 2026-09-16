# Pipeline Service

Вынесенный `PromptReviewPipeline` (`api/app/pipeline/`) как отдельный HTTP-сервис.

Компонент **опциональный**: по умолчанию развёртывание использует in-process backend (`BACKEND_TYPE=langchain`, LLM-вызовы в процессе API). Pipeline Service включается, когда нужно вынести LLM-нагрузку из процесса API.

## 💡 1. Зачем выносить

- **Изоляция отказов**: сбой/деградация LLM не блокирует event loop API-процесса.
- **Независимое масштабирование**: LLM-вызовы — тяжёлые; их можно масштабировать отдельно от тонкого API-шлюза.
- **Разделение развёртывания**: обновление промптов/пайплайна не требует пересборки API.

## 🔌 2. API

| Endpoint | Описание |
|----------|----------|
| `GET /health` | Health check: `{status, backend, model}` |
| `POST /process` | Полный цикл анализа: `PromptReviewRequest` → `PromptReviewResponse` |

JSON-контракт идентичен in-process режиму (`docs/API_CONTRACT.md`): включая `token_usage`, `processing_time_ms`, retry-конфигурацию (`RETRY_MAX_ATTEMPTS`) — всё наследуется из общего кода `api/app/pipeline/`.

## 🚀 3. Запуск локально

```bash
cd api
# переменные окружения (OPENAI_API_KEY или Ollama) — из ../infra/.env или export
PYTHONPATH=. uvicorn pipeline_service.main:app --port 8001
```

## 🚀 4. Запуск в Docker (опционально)

```bash
cd infra
docker compose -p infra -f docker-compose.pipeline.yml --profile pipeline up -d
curl http://localhost:8001/health
```

## 🔌 5. Включение в API

В `infra/.env`:

```env
BACKEND_TYPE=langchain_service
PIPELINE_SERVICE_URL=http://pipeline-service:8001
```

и перезапуск `docker-compose.api.yml`. При недоступности сервиса API отвечает `503 backend_unavailable`.

## 🏗️ 6. Архитектура

```
                 BACKEND_TYPE=langchain            BACKEND_TYPE=langchain_service
                          │                                      │
Web/Telegram/n8n ──► FastAPI (/review) ──► LangChainAdapter      PipelineServiceAdapter
                                            (in-process)                │ HTTP POST /process
                                                 │                      ▼
                                                 │            Pipeline Service
                                                 │            api/pipeline_service/
                                                 ▼                      │
                                            PromptReviewPipeline ◄──────┘
                                            api/app/pipeline/ (общий код)
```

Общий код (`pipeline`, `schemas`, `logger`, `config`, `llm.py`) — один, без дублирования: сервис собирается из того же build context `api/`.

---

**Статус:** актуален; сервис опционален (P5)
**Последнее обновление:** 2026-09-16
**История изменений:** [📝 CHANGE_LOG.md](../../docs/CHANGE_LOG.md#-1-история-изменений-документации)
