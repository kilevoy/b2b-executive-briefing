"""Unit tests for B2B Executive Briefing engine with multi-project breakdown."""

import asyncio
from briefing.crm_adapter import AmoCRMBriefingAdapter
from briefing.analyzer import PipelineAuditor
from briefing.telegram_formatter import TelegramBriefingFormatter
from briefing.scheduler import ExecutiveBriefingService
from briefing.models import DealRisk


def test_auditor_calculations():
    adapter = AmoCRMBriefingAdapter(mock_mode=True)
    raw_data = asyncio.run(adapter.fetch_pipeline_data())

    auditor = PipelineAuditor(stalled_threshold_days=5)
    report = auditor.analyze(raw_data)

    assert report.month_plan == 30_000_000.0
    assert report.month_fact == 21_850_000.0
    assert report.month_progress_pct > 70.0
    assert len(report.stalled_deals) == 4
    assert report.total_stalled_amount > 15_000_000.0

    # Проверка рисков
    top_deal = report.stalled_deals[0]
    assert top_deal.days_stalled >= 12
    assert "detail" in top_deal.url

    # Проверка лидерборда менеджеров (первый Алексей Власов)
    assert report.managers[0].name == "Алексей Власов"
    assert report.managers[0].plan_percent > 80.0


def test_telegram_formatter():
    adapter = AmoCRMBriefingAdapter(mock_mode=True)
    raw_data = asyncio.run(adapter.fetch_pipeline_data())
    auditor = PipelineAuditor()
    report = auditor.analyze(raw_data)

    formatter = TelegramBriefingFormatter()
    html = formatter.format_html(report)

    assert "УТРЕННИЙ ПУЛЬС ХОЛДИНГА" in html
    assert "Ангары и Здания" in html
    assert "Кровли и Фасады" in html
    assert "Газобетон" in html
    assert "ЗАВИСШИЕ СДЕЛКИ" in html
    assert "КОНТРОЛЬ ДЕБИТОРКИ (DSO)" in html
    assert "Алексей Власов" in html


def test_briefing_service_mock_dispatch():
    service = ExecutiveBriefingService(mock_mode=True)
    res = asyncio.run(service.generate_and_dispatch())

    assert res["status"] == "success"
    assert res["mode"] == "mock"
    assert "telegram_html" in res
    assert "report" in res
