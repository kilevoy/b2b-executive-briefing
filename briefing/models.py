"""Pydantic models for B2B Executive Briefing & Pipeline Auditor."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DealRisk(str, Enum):
    LOW = "LOW"           # 5-7 дней без движения
    MEDIUM = "MEDIUM"     # 8-14 дней без движения
    CRITICAL = "CRITICAL" # > 14 дней без движения (высокий риск потери лида)


class StalledDeal(BaseModel):
    """Сделка, зависшая на этапе воронки без активных действий."""
    id: int
    name: str
    client: str
    manager: str
    stage: str
    budget: float
    days_stalled: int
    risk: DealRisk
    url: str


class OverdueTask(BaseModel):
    """Просроченная задача менеджера."""
    id: int
    deal_name: str
    manager: str
    task_text: str
    days_overdue: int


class ReceivablesItem(BaseModel):
    """Пункт контроля дебиторской задолженности / постоплаты."""
    invoice_id: str
    client: str
    manager: str
    amount: float
    due_date: str
    days_overdue: int
    is_critical: bool = False


class ManagerStats(BaseModel):
    """Сводные показатели менеджера."""
    name: str
    active_deals_count: int
    pipeline_amount: float
    closed_this_month: float
    plan_amount: float
    plan_percent: float
    overdue_tasks_count: int
    stalled_deals_count: int


class DailyBriefingReport(BaseModel):
    """Полный ежедневный управленческий отчёт РОПу / Коммерческому директору."""
    report_date: str
    pipeline_name: str
    month_plan: float
    month_fact: float
    month_progress_pct: float
    month_forecast: float
    stalled_deals: List[StalledDeal] = Field(default_factory=list)
    total_stalled_amount: float = 0.0
    overdue_tasks: List[OverdueTask] = Field(default_factory=list)
    receivables: List[ReceivablesItem] = Field(default_factory=list)
    total_receivables_overdue: float = 0.0
    managers: List[ManagerStats] = Field(default_factory=list)
    executive_summary: str = ""
    action_items: List[str] = Field(default_factory=list)

