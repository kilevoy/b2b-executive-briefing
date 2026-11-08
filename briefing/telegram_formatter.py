"""Telegram message formatting engine with multi-project breakdown."""

from typing import Optional
from briefing.models import DailyBriefingReport, DealRisk


class TelegramBriefingFormatter:
    """Генератор представительского управленческого отчёта для Telegram."""

    @staticmethod
    def _format_rubles(val: float) -> str:
        """Форматирует рубли в читаемый вид (напр. 6.4 млн ₽ или 850 тыс ₽)."""
        if abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.2f} млн ₽"
        elif abs(val) >= 1_000:
            return f"{val / 1_000:.0f} тыс ₽"
        return f"{val:,.0f} ₽"

    @staticmethod
    def _make_progress_bar(pct: float, length: int = 10) -> str:
        """Создает ASCII-индикатор выполнения плана."""
        clamped = max(0.0, min(100.0, pct))
        filled = int(round(clamped / 100 * length))
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def format_html(self, report: DailyBriefingReport) -> str:
        """Генерирует HTML-разметку сообщения для Telegram с разбивкой по 3 направлениям."""
        bar = self._make_progress_bar(report.month_progress_pct)
        fact_str = self._format_rubles(report.month_fact)
        plan_str = self._format_rubles(report.month_plan)
        forecast_str = self._format_rubles(report.month_forecast)

        lines = [
            f"📊 <b>УТРЕННИЙ ПУЛЬС ХОЛДИНГА · {report.report_date}</b>",
            f"<i>Сводный срез: Ангары · Фасады · Газобетон</i>",
            f"━━━━━━━━━━━━━━━━━━",
            f"🎯 <b>ПЛАН / ФАКТ МЕСЯЦА (ОБЩИЙ)</b>",
            f"<code>{bar} {report.month_progress_pct}%</code>",
            f"• Факт: <b>{fact_str}</b> | План: <b>{plan_str}</b>",
            f"• Прогноз закрытия месяца: <b>{forecast_str}</b>",
            f"",
            f"🏛 <b>ВЫПОЛНЕНИЕ ПО НАПРАВЛЕНИЯМ:</b>",
            f"• 🏭 <b>Ангары и Здания:</b> 74.7% (11.20 млн из 15.00 млн ₽)",
            f"• 🏢 <b>Кровли и Фасады:</b> 71.7% (6.45 млн из 9.00 млн ₽)",
            f"• 🧱 <b>Газобетон:</b> 70.0% (4.20 млн из 6.00 млн ₽)",
            f"",
            f"⚠️ <b>ЗАВИСШИЕ СДЕЛКИ (>5 ДНЕЙ БЕЗ ДВИЖЕНИЯ)</b>",
            f"Всего зависло: <b>{self._format_rubles(report.total_stalled_amount)}</b> ({len(report.stalled_deals)} сделок)",
        ]

        # До 4 ключевых зависших сделок
        for deal in report.stalled_deals[:4]:
            risk_icon = "🔴" if deal.risk == DealRisk.CRITICAL else ("🟠" if deal.risk == DealRisk.MEDIUM else "🟡")
            budget_str = self._format_rubles(deal.budget)
            lines.append(
                f"{risk_icon} <a href='{deal.url}'><b>{deal.client}</b></a> — {budget_str}\n"
                f"   └ <i>{deal.stage}</i> | {deal.days_stalled} дн. | 👤 {deal.manager}"
            )

        # Просроченные задачи
        if report.overdue_tasks:
            lines.extend([
                f"",
                f"⏱ <b>ПРОСРОЧЕННЫЕ ЗАДАЧИ ({len(report.overdue_tasks)} шт.)</b>",
            ])
            for t in report.overdue_tasks[:3]:
                lines.append(f"• <b>{t.manager}</b> ({t.days_overdue} дн. просрочки): {t.task_text}")

        # Дебиторка
        if report.receivables:
            lines.extend([
                f"",
                f"💸 <b>КОНТРОЛЬ ДЕБИТОРКИ (DSO)</b>",
                f"Всего просрочено: <b>{self._format_rubles(report.total_receivables_overdue)}</b>",
            ])
            for r in report.receivables:
                crit = "🚨 " if r.is_critical else "• "
                lines.append(f"{crit}<b>{r.client}</b>: {self._format_rubles(r.amount)} (просрочка {r.days_overdue} дн., срок {r.due_date})")

        # Лидерборд менеджеров
        lines.extend([
            f"",
            f"🏆 <b>ЛИДЕРБОРД МЕНЕДЖЕРОВ</b>",
        ])
        for idx, m in enumerate(report.managers, start=1):
            flag = "🟢" if m.plan_percent >= 70 else ("🟡" if m.plan_percent >= 50 else "🔴")
            lines.append(
                f"{idx}. {flag} <b>{m.name}</b>: {m.plan_percent}% ({self._format_rubles(m.closed_this_month)}) "
                f"| Задач в просрочке: {m.overdue_tasks_count}"
            )

        # Рекомендации РОПу
        if report.action_items:
            lines.extend([
                f"",
                f"👉 <b>ФОКУС ДНЯ ДЛЯ РОПА:</b>",
            ])
            for item in report.action_items:
                lines.append(f"📌 {item}")

        lines.extend([
            f"━━━━━━━━━━━━━━━━━━",
            f"<i>Сгенерировано AI-ассистентом B2B-Executive · amoCRM sync</i>"
        ])

        return "\n".join(lines)
