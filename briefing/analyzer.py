"""Pipeline analysis engine: detects stalled deals, overdue tasks, receivables risks."""

from datetime import datetime
from typing import Dict, Any, List

from briefing.models import (
    DailyBriefingReport,
    StalledDeal,
    DealRisk,
    OverdueTask,
    ReceivablesItem,
    ManagerStats,
)


class PipelineAuditor:
    """Аналитический модуль для аудита воронки продаж и формирования управленческого отчёта."""

    def __init__(self, stalled_threshold_days: int = 5):
        self.stalled_threshold_days = stalled_threshold_days

    def analyze(self, raw_data: Dict[str, Any]) -> DailyBriefingReport:
        """Превращает сырые данные CRM в структурированный отчёт РОПа."""
        subdomain = raw_data.get("subdomain", "demo-b2b")
        pipeline_name = raw_data.get("pipeline_name", "Основная воронка")
        month_plan = float(raw_data.get("month_plan", 0.0))
        month_fact = float(raw_data.get("month_fact", 0.0))
        
        progress_pct = round((month_fact / month_plan * 100), 1) if month_plan > 0 else 0.0
        
        # Прогноз выполнения на конец месяца с учетом текущего темпа
        elapsed_pct = raw_data.get("days_elapsed_pct", 0.65)
        forecast = round((month_fact / elapsed_pct), 0) if elapsed_pct > 0 else month_fact

        # 1. Анализ зависших сделок
        stalled_deals: List[StalledDeal] = []
        total_stalled_amount = 0.0
        
        for item in raw_data.get("raw_stalled_deals", []):
            days = item.get("days_stalled", 0)
            if days >= self.stalled_threshold_days:
                budget = float(item.get("budget", 0.0))
                total_stalled_amount += budget

                if days >= 14:
                    risk = DealRisk.CRITICAL
                elif days >= 8:
                    risk = DealRisk.MEDIUM
                else:
                    risk = DealRisk.LOW

                deal_id = item.get("id", 0)
                deal_url = f"https://{subdomain}.amocrm.ru/leads/detail/{deal_id}"

                stalled_deals.append(
                    StalledDeal(
                        id=deal_id,
                        name=item.get("name", "Сделка"),
                        client=item.get("client", "Клиент"),
                        manager=item.get("manager", "Не назначен"),
                        stage=item.get("stage", "Этап"),
                        budget=budget,
                        days_stalled=days,
                        risk=risk,
                        url=deal_url,
                    )
                )

        # Сортировка зависших сделок по бюджету (убывание)
        stalled_deals.sort(key=lambda x: x.budget, reverse=True)

        # 2. Анализ просроченных задач
        overdue_tasks: List[OverdueTask] = []
        for item in raw_data.get("raw_overdue_tasks", []):
            overdue_tasks.append(
                OverdueTask(
                    id=item.get("id", 0),
                    deal_name=item.get("deal_name", ""),
                    manager=item.get("manager", ""),
                    task_text=item.get("task_text", ""),
                    days_overdue=item.get("days_overdue", 1),
                )
            )
        overdue_tasks.sort(key=lambda x: x.days_overdue, reverse=True)

        # 3. Анализ дебиторской задолженности
        receivables: List[ReceivablesItem] = []
        total_receivables_overdue = 0.0
        for item in raw_data.get("raw_receivables", []):
            amount = float(item.get("amount", 0.0))
            days = item.get("days_overdue", 0)
            if days > 0:
                total_receivables_overdue += amount

            receivables.append(
                ReceivablesItem(
                    invoice_id=item.get("invoice_id", ""),
                    client=item.get("client", ""),
                    manager=item.get("manager", ""),
                    amount=amount,
                    due_date=item.get("due_date", ""),
                    days_overdue=days,
                    is_critical=item.get("is_critical", False),
                )
            )

        # 4. Сводка по менеджерам
        managers: List[ManagerStats] = []
        for m in raw_data.get("managers", []):
            m_name = m.get("name", "")
            m_plan = float(m.get("plan", 1.0))
            m_fact = float(m.get("fact", 0.0))
            m_pct = round((m_fact / m_plan * 100), 1) if m_plan > 0 else 0.0

            m_overdue_count = sum(1 for t in overdue_tasks if t.manager == m_name)
            m_stalled_count = sum(1 for d in stalled_deals if d.manager == m_name)

            managers.append(
                ManagerStats(
                    name=m_name,
                    active_deals_count=m.get("active_deals", 0),
                    pipeline_amount=float(m.get("pipeline_sum", 0.0)),
                    closed_this_month=m_fact,
                    plan_amount=m_plan,
                    plan_percent=m_pct,
                    overdue_tasks_count=m_overdue_count,
                    stalled_deals_count=m_stalled_count,
                )
            )
        
        # Сортировка менеджеров по выполнению плана (лидеры сверху)
        managers.sort(key=lambda x: x.plan_percent, reverse=True)

        # 5. Выработка управленческих рекомендаций
        action_items: List[str] = []
        if total_stalled_amount > 10_000_000:
            action_items.append(
                f"Критичный объем зависших сделок ({total_stalled_amount:,.0f} ₽) — разобрать топ-3 сделки на утренней летучке."
            )
        if total_receivables_overdue > 0:
            action_items.append(
                f"Просроченная дебиторка {total_receivables_overdue:,.0f} ₽ — приостановить отгрузки до согласования графика оплат."
            )
        
        lagging_managers = [m.name for m in managers if m.plan_percent < 50.0]
        if lagging_managers:
            action_items.append(
                f"Отставание от плана у сотрудников: {', '.join(lagging_managers)} — проверить конверсию из КП в договор."
            )

        now_str = datetime.now().strftime("%d.%m.%Y")

        return DailyBriefingReport(
            report_date=now_str,
            pipeline_name=pipeline_name,
            month_plan=month_plan,
            month_fact=month_fact,
            month_progress_pct=progress_pct,
            month_forecast=forecast,
            stalled_deals=stalled_deals,
            total_stalled_amount=total_stalled_amount,
            overdue_tasks=overdue_tasks,
            receivables=receivables,
            total_receivables_overdue=total_receivables_overdue,
            managers=managers,
            executive_summary=(
                f"Выполнение плана: {progress_pct}% ({month_fact:,.0f} из {month_plan:,.0f} ₽). "
                f"В воронке зависло {len(stalled_deals)} сделок на сумму {total_stalled_amount:,.0f} ₽. "
                f"Просроченных задач: {len(overdue_tasks)}."
            ),
            action_items=action_items,
        )

