"""
FastAPI сервер для Prompt Review Service.

Эндпоинты:
- GET / - корневой endpoint
- GET /health - health check
- POST /review - анализ промпта
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
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
)
from .adapters import get_backend_adapter, BackendAdapter

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
    )


@app.post("/review", response_model=PromptReviewResponse)
async def review(request: PromptReviewRequest, req: Request):
    """
    Анализ промпта.

    Args:
        request: Запрос на анализ
        req: FastAPI Request (для доступа к app.state)

    Returns:
        PromptReviewResponse: Результат анализа

    Raises:
        HTTPException: При ошибках обработки
    """
    # Генерируем request_id если не указан
    request_id = request.request_id or f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

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
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
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