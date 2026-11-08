"""CRM adapter for extracting live pipeline and project metrics."""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


class AmoCRMBriefingAdapter:
    """Адаптер для выгрузки оперативных данных из amoCRM с разбивкой по 3 проектам."""

    def __init__(
        self,
        subdomain: Optional[str] = None,
        access_token: Optional[str] = None,
        mock_mode: Optional[bool] = None,
    ):
        self.subdomain = subdomain or os.getenv("AMOCRM_SUBDOMAIN", "demo-b2b")
        self.access_token = access_token or os.getenv("AMOCRM_ACCESS_TOKEN", "")
        
        env_mock = os.getenv("MOCK_MODE", "").lower() in ("true", "1", "yes")
        self.mock_mode = mock_mode if mock_mode is not None else (env_mock or not self.access_token)

    async def fetch_pipeline_data(self) -> Dict[str, Any]:
        """Получение данных CRM по проектам (Ангары, Фасады, Газобетон)."""
        if self.mock_mode:
            return self._generate_realistic_project_data()

        base_url = f"https://{self.subdomain}.amocrm.ru/api/v4"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            leads_resp = await client.get(f"{base_url}/leads?with=contacts,loss_reason&limit=250", headers=headers)
            leads_resp.raise_for_status()
            leads = leads_resp.json().get("_embedded", {}).get("leads", [])

            tasks_resp = await client.get(f"{base_url}/tasks?filter[is_completed]=0&limit=250", headers=headers)
            tasks_resp.raise_for_status()
            tasks = tasks_resp.json().get("_embedded", {}).get("tasks", [])

            users_resp = await client.get(f"{base_url}/users", headers=headers)
            users_resp.raise_for_status()
            users = users_resp.json().get("_embedded", {}).get("users", [])

            return {
                "leads": leads,
                "tasks": tasks,
                "users": users,
                "subdomain": self.subdomain,
            }

    def _generate_realistic_project_data(self) -> Dict[str, Any]:
        """Генерация реалистичного среза холдинга по 3 направлениям продаж."""
        return {
            "subdomain": self.subdomain,
            "company_name": "Производственно-строительный холдинг",
            "month_plan": 30_000_000.0,
            "month_fact": 21_850_000.0,
            "days_elapsed_pct": 0.68,  # 21-й день месяца
            "projects_summary": [
                {
                    "project_name": "🏭 Проект «Ангары и Здания»",
                    "plan": 15_000_000.0,
                    "fact": 11_200_000.0,
                    "progress_pct": 74.7,
                    "active_pipeline": 34_500_000.0,
                    "stalled_amount": 11_250_000.0,
                },
                {
                    "project_name": "🏢 Проект «Кровли и Фасады»",
                    "plan": 9_000_000.0,
                    "fact": 6_450_000.0,
                    "progress_pct": 71.7,
                    "active_pipeline": 18_200_000.0,
                    "stalled_amount": 3_200_000.0,
                },
                {
                    "project_name": "🧱 Проект «Автоклавный Газобетон»",
                    "plan": 6_000_000.0,
                    "fact": 4_200_000.0,
                    "progress_pct": 70.0,
                    "active_pipeline": 8_900_000.0,
                    "stalled_amount": 2_150_000.0,
                },
            ],
            "managers": [
                {
                    "name": "Алексей Власов",
                    "project": "🏭 Ангары",
                    "plan": 8_000_000.0,
                    "fact": 6_800_000.0,
                    "active_deals": 12,
                    "pipeline_sum": 19_500_000.0,
                },
                {
                    "name": "Дмитрий Морозов",
                    "project": "🏭 Ангары",
                    "plan": 7_000_000.0,
                    "fact": 4_400_000.0,
                    "active_deals": 10,
                    "pipeline_sum": 15_000_000.0,
                },
                {
                    "name": "Елена Смирнова",
                    "project": "🏢 Фасады",
                    "plan": 9_000_000.0,
                    "fact": 6_450_000.0,
                    "active_deals": 14,
                    "pipeline_sum": 18_200_000.0,
                },
                {
                    "name": "Михаил Карпов",
                    "project": "🧱 Газобетон",
                    "plan": 6_000_000.0,
                    "fact": 4_200_000.0,
                    "active_deals": 9,
                    "pipeline_sum": 8_900_000.0,
                },
            ],
            "raw_stalled_deals": [
                {
                    "id": 104521,
                    "name": "Металлокаркас логистического терминала 2400 м²",
                    "client": "ООО «ПромРесурс»",
                    "project": "🏭 Ангары",
                    "manager": "Дмитрий Морозов",
                    "stage": "Согласование проекта КМ",
                    "budget": 7_500_000.0,
                    "days_stalled": 12,
                },
                {
                    "id": 104889,
                    "name": "Быстровозводимый тёплый склад 1200 м²",
                    "client": "ЗАО «УралКомплект»",
                    "project": "🏭 Ангары",
                    "manager": "Дмитрий Морозов",
                    "stage": "КП отправлено (нет звонка)",
                    "budget": 3_750_000.0,
                    "days_stalled": 8,
                },
                {
                    "id": 105120,
                    "name": "Фасадные кассеты КФ-1 для ТРК (3500 м²)",
                    "client": "ГК «Строительный Альянс»",
                    "project": "🏢 Фасады",
                    "manager": "Елена Смирнова",
                    "stage": "Раскладка кассет и образцы",
                    "budget": 3_200_000.0,
                    "days_stalled": 6,
                },
                {
                    "id": 105304,
                    "name": "Газобетон D500 400мм (120 м³) на коттеджный посёлок",
                    "client": "ООО «Квартал-Строй»",
                    "project": "🧱 Газобетон",
                    "manager": "Михаил Карпов",
                    "stage": "Выставлен счёт на оплату",
                    "budget": 2_150_000.0,
                    "days_stalled": 7,
                },
            ],
            "raw_overdue_tasks": [
                {
                    "id": 5012,
                    "deal_name": "Металлокаркас логистического терминала",
                    "manager": "Дмитрий Морозов",
                    "task_text": "Уточнить у гл. инженера правки по разделу КМ",
                    "days_overdue": 4,
                },
                {
                    "id": 5045,
                    "deal_name": "Фасадные кассеты КФ-1 для ТРК",
                    "manager": "Елена Смирнова",
                    "task_text": "Отправить колор-карту RAL заказчику",
                    "days_overdue": 2,
                },
                {
                    "id": 5088,
                    "deal_name": "Газобетон D500 на объект",
                    "manager": "Михаил Карпов",
                    "task_text": "Проверить согласование графика длинномеров",
                    "days_overdue": 3,
                },
            ],
            "raw_receivables": [
                {
                    "invoice_id": "СФ-2026/304",
                    "client": "ООО «ТехноПромСервис»",
                    "manager": "Алексей Власов",
                    "amount": 1_650_000.0,
                    "due_date": "04.11.2026",
                    "days_overdue": 4,
                    "is_critical": True,
                },
                {
                    "invoice_id": "СФ-2026/318",
                    "client": "ЗАО «СтройВектор»",
                    "manager": "Михаил Карпов",
                    "amount": 780_000.0,
                    "due_date": "06.11.2026",
                    "days_overdue": 2,
                    "is_critical": False,
                },
            ],
        }
