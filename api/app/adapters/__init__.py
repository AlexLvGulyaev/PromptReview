"""
Backend-адаптеры для Prompt Review Service.

Позволяют переключаться между LangFlow и LangChain через конфигурацию.
"""

from .base import BackendAdapter
from .langflow import LangFlowAdapter
from .langchain import LangChainAdapter


def get_backend_adapter() -> BackendAdapter:
    """
    Фабрика адаптеров.

    Возвращает нужный адаптер в зависимости от BACKEND_TYPE:
    - langflow: LangFlowAdapter
    - langchain: LangChainAdapter
    """
    from app.config import settings

    if settings.BACKEND_TYPE == "langflow":
        return LangFlowAdapter(
            url=settings.LANGFLOW_URL,
            flow_id=settings.LANGFLOW_FLOW_ID,
            api_key=settings.LANGFLOW_API_KEY,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
    elif settings.BACKEND_TYPE == "langchain":
        return LangChainAdapter(
            model=settings.LANGCHAIN_MODEL,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
    else:
        raise ValueError(f"Unknown BACKEND_TYPE: {settings.BACKEND_TYPE}")


__all__ = [
    "BackendAdapter",
    "LangFlowAdapter",
    "LangChainAdapter",
    "get_backend_adapter",
]