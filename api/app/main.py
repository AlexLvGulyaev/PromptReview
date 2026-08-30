"""
FastAPI сервер для Prompt Review Service.

Эндпоинты:
- GET / - корневой endpoint
- GET /health - health check
- POST /review - анализ промпта
- POST /demo/start - новая демо-сессия (DEMO_MODE)
- GET /demo/status - состояние демо-сессии (DEMO_MODE)
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .logger import get_logger
from .schemas import (
    PromptReviewRequest,
    PromptReviewResponse,
    ErrorResponse,
    HealthResponse,
    DemoStartResponse,
    DemoStatusResponse,
)
from .adapters import get_backend_adapter, BackendAdapter
from .demo import (
    get_client_ip,
    is_demo_mode_enabled,
    require_demo_session,
    store,
)

logger = get_logger(__name__)


# Глобальный адаптер (инициализируется в lifespan)
backend_adapter: Optional[BackendAdapter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    global backend_adapter
    logger.info(
        f"Starting Prompt Review Service with BACKEND_TYPE={settings.BACKEND_TYPE}"
    )
    try:
        backend_adapter = get_backend_adapter()
        logger.info("Backend adapter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize backend adapter: {e}")
        raise

    yield

    # Shutdown
    if backend_adapter and hasattr(backend_adapter, "close"):
        await backend_adapter.close()
    logger.info("Prompt Review Service stopped")


# Создаём приложение
app = FastAPI(
    title="Prompt Review Service",
    description="AI-сервис для анализа качества промптов",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============================================================================
# STATIC FILES (Web UI)
# ============================================================================

# Монтируем Web UI как статические файлы
# Путь к Web UI: ../web относительно app/main.py
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(web_dir), html=True), name="ui")
    logger.info(f"Web UI mounted at /ui from {web_dir}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """
    Корневой endpoint.

    Returns:
        dict: {"status": "up"}
    """
    return {"status": "up"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check для мониторинга.

    Returns:
        HealthResponse: Статус сервиса и доступность backend
    """
    backend_available = False
    if backend_adapter:
        try:
            backend_available = await backend_adapter.health_check()
        except Exception as e:
            logger.warning(f"Backend health check failed: {e}")

    return HealthResponse(
        status="ok",
        backend=settings.BACKEND_TYPE,
        backend_available=backend_available,
        demo_mode=settings.DEMO_MODE,
    )


@app.post("/review", response_model=PromptReviewResponse)
async def review(request: PromptReviewRequest, req: Request, response: Response):
    """
    Анализ промпта.

    При включённом DEMO_MODE требует заголовок x-demo-token (демо-сессия),
    списывает один запрос из квоты и возвращает остаток в заголовке
    X-Demo-Requests-Remaining.

    Args:
        request: Запрос на анализ
        req: FastAPI Request (клиент, заголовки)
        response: Response (демо-заголовки остатка квоты)

    Returns:
        PromptReviewResponse: Результат анализа

    Raises:
        HTTPException: При ошибках обработки
    """
    # Генерируем request_id если не указан
    request_id = request.request_id or f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    # Demo mode: проверка токена и списание квоты до похода в LLM
    if is_demo_mode_enabled():
        demo_session = await require_demo_session(req)
        response.headers["X-Demo-Requests-Remaining"] = str(demo_session.requests_remaining)

    # Логируем входящий запрос
    logger.info(
        f"Review request received",
        extra={
            "request_id": request_id,
            "user_id": request.user_id,
            "source": request.source.value,
            "prompt_length": len(request.prompt_text),
        }
    )

    start_time = time.time()

    try:
        # Вызываем backend adapter
        response = await backend_adapter.review(request)
        response.request_id = request_id
        response.processing_time_ms = int((time.time() - start_time) * 1000)

        # Логируем успешный результат
        logger.info(
            f"Review completed",
            extra={
                "request_id": request_id,
                "user_id": request.user_id,
                "is_prompt": response.is_prompt,
                "quality_level": response.quality_level.value,
                "processing_time_ms": response.processing_time_ms,
            }
        )

        return response

    except RuntimeError as e:
        # Ошибка backend (timeout, connection error)
        logger.error(
            f"Backend error: {e}",
            extra={"request_id": request_id, "user_id": request.user_id}
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "backend_unavailable",
                "message": str(e),
            }
        )

    except Exception as e:
        # Неожиданная ошибка
        logger.exception(
            f"Unexpected error: {e}",
            extra={"request_id": request_id, "user_id": request.user_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            }
        )


# ============================================================================
# DEMO SESSION ENDPOINTS (public Web UI, DEMO_MODE)
# ============================================================================


def _ensure_demo_enabled() -> None:
    """Запретить demo-эндпоинты, если DEMO_MODE выключен."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "demo_mode_disabled",
                "message": "Demo mode is not enabled on this instance",
            },
        )


@app.post("/demo/start", response_model=DemoStartResponse)
async def demo_start(req: Request):
    """
    Создать новую демо-сессию для Web UI.

    Возвращает opaque-токен, который нужно передавать в заголовке
    ``x-demo-token`` на каждый POST /review. Ограничено лимитом
    сессий с одного IP (DEMO_MAX_SESSIONS_PER_IP_PER_HOUR).
    """
    _ensure_demo_enabled()
    session = await store.create_session(client_ip=get_client_ip(req))
    return DemoStartResponse(
        token=session.token,
        requests_limit=session.requests_limit,
        requests_remaining=session.requests_limit,
        expires_at=session.expires_at.isoformat(),
        interval_seconds=settings.DEMO_MIN_REQUEST_INTERVAL_SECONDS,
    )


@app.get("/demo/status", response_model=DemoStatusResponse)
async def demo_status(req: Request):
    """
    Состояние демо-сессии: остаток квоты и время истечения.

    Токен читается из заголовка ``x-demo-token``.
    """
    _ensure_demo_enabled()
    token = req.headers.get("x-demo-token")
    session = await store.get_status(token)
    return DemoStatusResponse(
        token=session.token,
        requests_used=session.requests_used,
        requests_limit=session.requests_limit,
        requests_remaining=session.requests_remaining,
        expires_at=session.expires_at.isoformat() if session.expires_at else "",
        is_active=session.is_active and not session.is_expired,
    )


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers or {},
        content={
            "error": exc.detail.get("error", "http_error") if isinstance(exc.detail, dict) else "http_error",
            "message": exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
            "details": exc.detail.get("details", {}) if isinstance(exc.detail, dict) else {},
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик всех остальных исключений."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": {},
        }
    )


# ============================================================================
# STARTUP INFO
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )