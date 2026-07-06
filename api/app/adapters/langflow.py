"""
LangFlow Adapter для Prompt Review Service.

Вызывает LangFlow через HTTP API и ожидает структурированный JSON-ответ.
"""

import time
import uuid
import json
import re
from typing import Optional
import httpx

from ..schemas import (
    PromptReviewRequest,
    PromptReviewResponse,
    PromptMetrics,
    PromptScores,
    QualityLevel,
    Recommendation,
)
from .base import BackendAdapter
from ..logger import get_logger

logger = get_logger(__name__)


class LangFlowAdapter(BackendAdapter):
    """
    Адаптер для вызова LangFlow через HTTP API.

    LangFlow должен быть настроен на возврат Structured Output
    с JSON-контрактом, соответствующим PromptReviewResponse.
    """

    def __init__(
        self,
        url: str,
        flow_id: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Инициализация адаптера.

        Args:
            url: URL LangFlow сервера (например, https://langflow.example.com)
            flow_id: ID Flow в LangFlow
            api_key: API ключ LangFlow (опционально)
            timeout: Timeout запроса в секундах
        """
        self.url = url.rstrip("/")
        self.flow_id = flow_id
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def review(self, request: PromptReviewRequest) -> PromptReviewResponse:
        """
        Выполнить анализ промпта через LangFlow API.

        Args:
            request: Запрос на анализ

        Returns:
            PromptReviewResponse: Результат анализа
        """
        start_time = time.time()
        request_id = request.request_id or f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

        # Рассчитываем метрики локально (как в PEl05)
        metrics = self._calculate_metrics(request.prompt_text)

        try:
            # Формируем запрос к LangFlow
            # Используем output_type="any" и output_component для получения чистого JSON
            # без Chat Output и без markdown-обёртки
            url = f"{self.url}/api/v1/run/{self.flow_id}"
            payload = {
                "input_value": request.prompt_text,
                "input_type": "chat",
                "output_type": "any",
                "session_id": f"session_{request.user_id}",
            }

            # Пробуем разные способы авторизации
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                # LangFlow поддерживает разные способы авторизации
                # Пробуем Bearer token
                auth_headers = [
                    {"Authorization": f"Bearer {self.api_key}"},
                    {"x-api-key": self.api_key},
                ]
            else:
                auth_headers = [{}]

            last_error = None
            for auth_header in auth_headers:
                try:
                    response = await self.client.post(
                        url,
                        json=payload,
                        headers={**headers, **auth_header},
                    )
                    response.raise_for_status()
                    data = response.json()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (401, 403):
                        # Пробуем следующий способ авторизации
                        last_error = e
                        continue
                    raise
            else:
                # Ни один способ авторизации не сработал
                raise last_error or httpx.HTTPStatusError(
                    "LangFlow auth failed",
                    request=None,
                    response=None,
                )

            # Парсим ответ LangFlow
            result = self._parse_langflow_response(data, request, metrics, start_time)
            return result

        except httpx.TimeoutException as e:
            logger.error(f"LangFlow timeout: {e}")
            raise RuntimeError(f"LangFlow request timeout: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"LangFlow request error: {e}")
            raise RuntimeError(f"LangFlow request error: {e}") from e
        except Exception as e:
            logger.error(f"LangFlow unexpected error: {e}")
            raise RuntimeError(f"LangFlow unexpected error: {e}") from e

    async def health_check(self) -> bool:
        """
        Проверить доступность LangFlow.

        Returns:
            bool: True если LangFlow доступен
        """
        try:
            url = f"{self.url}/health_check"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def _calculate_metrics(self, text: str) -> PromptMetrics:
        """
        Рассчитать метрики промпта.

        Соответствует collectPromptMetrics из PEl05.
        """
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        words = text.split()
        markdown_headings = [line for line in lines if line.strip().startswith("#")]
        bullet_items = [line for line in lines if line.strip().startswith(("-", "*", "+"))]
        numbered_items = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
        markdown_tables = [line for line in lines if "|" in line and line.strip().startswith("|")]
        xml_tags = text.count("<") + text.count("/>")
        code_blocks = text.count("```") // 2
        max_line_length = max((len(line) for line in lines), default=0)
        avg_line_length = (
            int(sum(len(line) for line in non_empty_lines) / len(non_empty_lines))
            if non_empty_lines
            else 0
        )

        return PromptMetrics(
            characters=len(text),
            words=len(words),
            lines=len(lines),
            non_empty_lines=len(non_empty_lines),
            markdown_headings=len(markdown_headings),
            bullet_items=len(bullet_items),
            numbered_items=len(numbered_items),
            markdown_table_lines=len(markdown_tables),
            xml_tags=xml_tags,
            code_blocks=code_blocks,
            max_line_length=max_line_length,
            avg_line_length=avg_line_length,
        )

    def _parse_langflow_response(
        self,
        data: dict,
        request: PromptReviewRequest,
        metrics: PromptMetrics,
        start_time: float,
    ) -> PromptReviewResponse:
        """
        Парсить ответ LangFlow в PromptReviewResponse.

        LangFlow возвращает JSON в формате Structured Output.
        """
        processing_time_ms = int((time.time() - start_time) * 1000)
        request_id = request.request_id or f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

        # LangFlow возвращает результат в нескольких форматах:
        # 1. artifacts.structured_output.raw — чистый JSON (рекомендуется)
        # 2. results.message.text — JSON с markdown-обёрткой
        result_data = None

        logger.debug(f"Parsing LangFlow response, keys: {list(data.keys())}")

        # Путь 1: Structured Output через artifacts (рекомендуется)
        try:
            result_data = data["outputs"][0]["outputs"][0]["artifacts"]["structured_output"]["raw"]
            logger.debug("Found structured_output.raw")
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(f"No structured_output.raw: {e}")

        # Путь 2: Chat Output с markdown-обёрткой
        if result_data is None:
            try:
                outputs = data["outputs"][0]["outputs"][0]
                logger.debug(f"outputs keys: {list(outputs.keys())}")

                message_obj = outputs["results"]["message"]
                logger.debug(f"message_obj type: {type(message_obj).__name__}")

                # message_obj может быть dict с полем text или строкой
                if isinstance(message_obj, dict):
                    raw = message_obj.get("text")
                    if not raw:
                        data_obj = message_obj.get("data")
                        if isinstance(data_obj, dict):
                            raw = data_obj.get("text", "")
                    logger.debug(f"Got raw text from dict, length: {len(raw) if raw else 0}")
                elif isinstance(message_obj, str):
                    raw = message_obj
                    logger.debug(f"Got raw string, length: {len(raw)}")
                else:
                    raw = None
                    logger.debug(f"message_obj is neither dict nor str: {type(message_obj)}")

                # Очищаем markdown-обёртку (как в n8n)
                if isinstance(raw, str) and raw:
                    raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
                    raw = re.sub(r'^```\s*', '', raw, flags=re.IGNORECASE)
                    raw = re.sub(r'```$', '', raw, flags=re.IGNORECASE)
                    raw = raw.strip()
                    result_data = json.loads(raw)
                    logger.debug("Successfully parsed JSON from markdown")
            except (KeyError, IndexError, TypeError, json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Path 2 parsing error: {e}")

        # Путь 3: Прямой JSON ответ
        if result_data is None:
            try:
                result_data = data["result"]
                logger.debug("Found data['result']")
            except (KeyError, TypeError) as e:
                logger.debug(f"No data['result']: {e}")

        # Путь 4: Весь ответ как есть
        if result_data is None:
            result_data = data
            logger.debug("Using entire response as result_data")

        # Формируем ответ
        # Если LangFlow вернул структурированный JSON, используем его
        # Иначе формируем базовый ответ
        if isinstance(result_data, dict):
            is_prompt = result_data.get("is_prompt", True)

            if is_prompt:
                # Промпт - формируем полный ответ
                scores_data = result_data.get("scores", {})
                scores = PromptScores(
                    clarity=scores_data.get("clarity", 0),
                    completeness=scores_data.get("completeness", 0),
                    ambiguity_absence=scores_data.get("ambiguity_absence", 0),
                    target_audience_fit=scores_data.get("target_audience_fit", 0),
                    output_format=scores_data.get("output_format", 0),
                    constraints_quality=scores_data.get("constraints_quality", 0),
                    missing_assumptions=scores_data.get("missing_assumptions", 0),
                    structure_reusability=scores_data.get("structure_reusability", 0),
                    overall=scores_data.get("overall", 0),
                )

                recommendations_data = result_data.get("recommendations", [])
                # recommendations может быть списком строк или списком объектов
                recommendations = []
                for r in recommendations_data:
                    if isinstance(r, dict):
                        recommendations.append(Recommendation(
                            priority=r.get("priority", "medium"),
                            text=r.get("text", str(r))
                        ))
                    elif isinstance(r, str):
                        recommendations.append(Recommendation(
                            priority="medium",
                            text=r
                        ))
                    else:
                        logger.debug(f"Unknown recommendation type: {type(r)}")
                        recommendations.append(Recommendation(
                            priority="medium",
                            text=str(r)
                        ))

                quality_level_str = result_data.get("quality_level", "good").lower()
                quality_level_map = {
                    "excellent": QualityLevel.EXCELLENT,
                    "good": QualityLevel.GOOD,
                    "fair": QualityLevel.FAIR,
                    "acceptable": QualityLevel.FAIR,  # backward compatibility
                    "poor": QualityLevel.POOR,
                    "weak": QualityLevel.POOR,  # backward compatibility
                    "unusable": QualityLevel.POOR,  # backward compatibility
                }
                quality_level = quality_level_map.get(quality_level_str, QualityLevel.GOOD)

                return PromptReviewResponse(
                    request_id=request_id,
                    user_id=request.user_id,
                    is_prompt=True,
                    purpose=result_data.get("purpose"),
                    strengths=result_data.get("strengths", []),
                    weaknesses=result_data.get("weaknesses", []),
                    recommendations=recommendations,
                    scores=scores,
                    quality_level=quality_level,
                    revised_prompt=result_data.get("revised_prompt"),
                    metrics=metrics,
                    processing_time_ms=processing_time_ms,
                )
            else:
                # Не промпт
                return PromptReviewResponse(
                    request_id=request_id,
                    user_id=request.user_id,
                    is_prompt=False,
                    reason=result_data.get("reason", "Текст не является промптом"),
                    conversion_options=result_data.get("conversion_options", [
                        "Добавьте ролевую инструкцию (например: \"Ты — ...\")",
                        "Укажите ожидаемый формат результата",
                        "Опишите конкретную задачу",
                    ]),
                    quality_level=QualityLevel.NOT_APPLICABLE,
                    metrics=metrics,
                    processing_time_ms=processing_time_ms,
                )

        # Fallback: если не удалось распарсить
        return PromptReviewResponse(
            request_id=request_id,
            user_id=request.user_id,
            is_prompt=True,
            purpose="Анализ не удался",
            strengths=[],
            weaknesses=["Не удалось получить структурированный ответ от LangFlow"],
            recommendations=[],
            scores=PromptScores(
                clarity=0,
                completeness=0,
                ambiguity_absence=0,
                target_audience_fit=0,
                output_format=0,
                constraints_quality=0,
                missing_assumptions=0,
                structure_reusability=0,
                overall=0,
            ),
            quality_level=QualityLevel.POOR,
            metrics=metrics,
            processing_time_ms=processing_time_ms,
        )

    async def close(self):
        """Закрыть HTTP клиент."""
        await self.client.aclose()