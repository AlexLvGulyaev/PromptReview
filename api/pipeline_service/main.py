"""
Pipeline Service — вынесенный PromptReviewPipeline как отдельный HTTP-сервис.

Тонкая обёртка над api/app/pipeline/: тот же конвейер, те же схемы, тот же
JSON-контракт. Используется при BACKEND_TYPE=langchain_service в API —
LLM-вызовы уходят из процесса API в отдельный контейнер.

Запуск (локально):
    cd api && PYTHONPATH=. uvicorn pipeline_service.main:app --port 8001

JSON-контракт:
    POST /process: PromptReviewRequest → PromptReviewResponse
    GET  /health:  {status, backend, model}
"""

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.logger import get_logger
from app.pipeline import PromptReviewPipeline
from app.pipeline.llm import create_llm
from app.schemas import PromptReviewRequest, PromptReviewResponse

logger = get_logger(__name__)

app = FastAPI(
    title="Prompt Review Pipeline Service",
    description="Вынесенный PromptReviewPipeline: классификация, анализ и улучшение промптов (LLM)",
    version="1.0.0",
)

# Ленивая инициализация LLM и pipeline (один экземпляр на процесс)
_llm = None
_pipeline: PromptReviewPipeline | None = None


def _get_pipeline() -> PromptReviewPipeline:
    """Получить или создать pipeline (LLM инициализируется лениво)."""
    global _llm, _pipeline
    if _pipeline is None:
        _llm = create_llm(
            model=settings.LANGCHAIN_MODEL,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
        _pipeline = PromptReviewPipeline(llm=_llm)
    return _pipeline


@app.get("/health")
async def health():
    """Health check: конфигурация LLM должна быть полной."""
    try:
        _get_pipeline()
    except ValueError as e:
        return {"status": "error", "backend": "langchain", "message": str(e)}
    return {
        "status": "ok",
        "backend": "langchain",
        "model": settings.LANGCHAIN_MODEL,
    }


@app.post("/process", response_model=PromptReviewResponse)
async def process(request: PromptReviewRequest) -> PromptReviewResponse:
    """Полный цикл анализа промпта (тот же контракт, что у in-process backend)."""
    try:
        return await _get_pipeline().process(request)
    except ValueError as e:
        # Ошибка конфигурации LLM (нет ключа, неизвестный провайдер)
        raise HTTPException(status_code=503, detail={"error": "backend_unavailable", "message": str(e)})
    except Exception as e:
        logger.exception(
            "Pipeline Service processing failed",
            extra={"request_id": request.request_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": str(e)})