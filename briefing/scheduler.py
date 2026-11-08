"""Scheduler module for running daily briefings at 08:45 AM."""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx

from briefing.crm_adapter import AmoCRMBriefingAdapter
from briefing.analyzer import PipelineAuditor
from briefing.telegram_formatter import TelegramBriefingFormatter

logger = logging.getLogger(__name__)


class ExecutiveBriefingService:
    """Сервис сбора, анализа и рассылки ежедневного брифинга."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        mock_mode: Optional[bool] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        
        env_mock = os.getenv("MOCK_MODE", "").lower() in ("true", "1", "yes")
        self.mock_mode = mock_mode if mock_mode is not None else (env_mock or not self.bot_token)

        self.crm_adapter = AmoCRMBriefingAdapter(mock_mode=self.mock_mode)
        self.auditor = PipelineAuditor()
        self.formatter = TelegramBriefingFormatter()

    async def generate_and_dispatch(self) -> Dict[str, Any]:
        """Формирует отчёт и отправляет его в Telegram."""
        # 1. Получение данных CRM
        raw_data = await self.crm_adapter.fetch_pipeline_data()

        # 2. Анализ воронки
        report = self.auditor.analyze(raw_data)

        # 3. Форматирование текста
        message_html = self.formatter.format_html(report)

        # 4. Отправка в Telegram
        if self.mock_mode:
            logger.info("ExecutiveBriefingService [MOCK MODE]: Отчёт успешно сгенерирован.")
            return {
                "status": "success",
                "mode": "mock",
                "report": report.model_dump(),
                "telegram_html": message_html,
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return {
                "status": "success",
                "mode": "live",
                "telegram_response": resp.json(),
                "report": report.model_dump(),
            }

