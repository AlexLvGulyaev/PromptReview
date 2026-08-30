"""
Demo session limiter для публичного Web UI.

Реализация паттерна `web-ui-tokenized-demo-limiter` (Source Case: ai-curator)
на in-memory-хранилище: у Prompt Review Service нет базы данных, а демо-сессии
эфемерны (TTL ~1 час), поэтому состояние держится в процессе API.

Три уровня ограничений:
1. Максимум демо-сессий с одного IP за час (защита от массового создания).
2. Минимальный интервал между запросами одной сессии (rate limit).
3. Квота запросов на сессию.

Backend — единственный источник правды по квотам: токен обязателен
в заголовке ``x-demo-token`` на POST /review, когда включён DEMO_MODE.
"""

import asyncio
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, Request, status

from .config import settings


@dataclass
class DemoSession:
    """Демо-сессия с квотой запросов."""

    token: str
    client_ip: Optional[str] = None
    requests_used: int = 0
    requests_limit: int = 20
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_request_at: Optional[datetime] = None

    @property
    def requests_remaining(self) -> int:
        return max(0, self.requests_limit - self.requests_used)

    @property
    def is_expired(self) -> bool:
        return self.expires_at is None or self.expires_at <= datetime.now(timezone.utc)


class DemoLimiterStore:
    """In-memory-хранилище демо-сессий с атомарными операциями."""

    def __init__(self):
        self._sessions: Dict[str, DemoSession] = {}
        # Лог создания сессий по IP: ip -> [created_at, ...]
        self._ip_history: Dict[str, List[datetime]] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, client_ip: Optional[str]) -> DemoSession:
        """Создать новую демо-сессию.

        Raises:
            HTTPException(429): слишком много сессий с этого IP за час.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Уровень 1: лимит сессий на IP
            if (
                settings.DEMO_MAX_SESSIONS_PER_IP_PER_HOUR > 0
                and client_ip
            ):
                self._prune_ip_history(client_ip, now)
                recent = self._ip_history.get(client_ip, [])
                if len(recent) >= settings.DEMO_MAX_SESSIONS_PER_IP_PER_HOUR:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "demo_session_limit",
                            "message": (
                                "Слишком много демо-сессий с этого IP. "
                                "Попробуйте позже."
                            ),
                        },
                    )

            session = DemoSession(
                token=secrets.token_hex(32),
                client_ip=client_ip,
                requests_limit=settings.DEMO_MAX_REQUESTS_PER_SESSION,
                expires_at=now + timedelta(minutes=settings.DEMO_SESSION_TTL_MINUTES),
            )
            self._sessions[session.token] = session
            if client_ip:
                self._ip_history.setdefault(client_ip, []).append(now)

            # Ленивая чистка протухших сессий при каждом создании
            self._cleanup_expired_locked()
            return session

    async def check_and_record_request(self, token: Optional[str]) -> DemoSession:
        """Провалидировать токен и списать один запрос из квоты.

        Raises:
            HTTPException(403): токен отсутствует или неизвестен.
            HTTPException(401): сессия истекла.
            HTTPException(429): rate limit или квота исчерпана.
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "demo_token_missing",
                    "message": "Требуется демо-токен. Перезагрузите страницу, чтобы начать демо-сессию.",
                },
            )

        async with self._lock:
            session = self._sessions.get(token)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "demo_token_invalid",
                        "message": "Демо-токен недействителен. Начните новую демо-сессию.",
                    },
                )

            if not session.is_active or session.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "demo_session_expired",
                        "message": "Демо-сессия истекла. Нажмите «Новая демо-сессия».",
                    },
                )

            now = datetime.now(timezone.utc)

            # Уровень 2: минимальный интервал между запросами
            if session.last_request_at is not None:
                elapsed = (now - session.last_request_at).total_seconds()
                if elapsed < settings.DEMO_MIN_REQUEST_INTERVAL_SECONDS:
                    retry_after = int(
                        settings.DEMO_MIN_REQUEST_INTERVAL_SECONDS - elapsed
                    ) + 1
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "demo_rate_limit",
                            "message": (
                                "Слишком часто. Подождите "
                                f"{retry_after} с перед следующим запросом."
                            ),
                        },
                        headers={"Retry-After": str(retry_after)},
                    )

            # Уровень 3: квота на сессию
            if session.requests_used >= session.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "demo_quota_exhausted",
                        "message": "Квота демо-сессии исчерпана. Нажмите «Новая демо-сессия».",
                    },
                )

            session.requests_used += 1
            session.last_request_at = now
            return session

    async def get_status(self, token: Optional[str]) -> DemoSession:
        """Текущее состояние сессии (без списания квоты)."""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "demo_token_missing",
                    "message": "Требуется заголовок x-demo-token.",
                },
            )
        async with self._lock:
            session = self._sessions.get(token)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "demo_session_not_found",
                        "message": "Демо-сессия не найдена.",
                    },
                )
            return session

    def get_session_snapshot(self, token: str) -> Optional[DemoSession]:
        """Синхронный снимок сессии для чтения полей (например, в /review)."""
        return self._sessions.get(token)

    def _cleanup_expired_locked(self) -> None:
        """Удалить протухшие сессии и устаревшую историю IP (вызвать под lock)."""
        stale = [t for t, s in self._sessions.items() if s.is_expired]
        for token in stale:
            del self._sessions[token]

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        for ip in list(self._ip_history.keys()):
            self._ip_history[ip] = [
                ts for ts in self._ip_history[ip] if ts >= cutoff
            ]
            if not self._ip_history[ip]:
                del self._ip_history[ip]

    def _prune_ip_history(self, ip: str, now: datetime) -> None:
        """Оставить в истории IP только сессии за последний час."""
        cutoff = now - timedelta(hours=1)
        history = self._ip_history.get(ip)
        if history is not None:
            self._ip_history[ip] = [ts for ts in history if ts >= cutoff]


# Глобальное хранилище (жизненный цикл — процесс API)
store = DemoLimiterStore()


def get_client_ip(request: Request) -> Optional[str]:
    """Реальный IP клиента из прокси-заголовков или соединения."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client = forwarded.split(",")[0].strip()
        if client:
            return client
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None
    if request.client:
        return request.client.host
    return None


async def require_demo_session(request: Request) -> DemoSession:
    """Проверить демо-токен и списать один запрос из квоты.

    Вызывается в POST /review, когда включён DEMO_MODE.
    """
    token = request.headers.get("x-demo-token")
    return await store.check_and_record_request(token)


def is_demo_mode_enabled() -> bool:
    """Demo mode включён, если установлен флаг DEMO_MODE=true."""
    return settings.DEMO_MODE


def monotonic_ts() -> float:
    """Монотонные часы для внутренних замеров (не входит в контракт API)."""
    return time.monotonic()