"""Command-line interface for manual trigger and preview."""

import asyncio
import argparse
from briefing.scheduler import ExecutiveBriefingService


def main():
    parser = argparse.ArgumentParser(description="B2B Executive Daily Briefing")
    parser.add_argument("--send", action="store_true", help="Отправить отчёт в Telegram")
    parser.add_argument("--preview", action="store_true", default=True, help="Вывести отчёт в консоль")

    args = parser.parse_args()

    async def _run():
        service = ExecutiveBriefingService(mock_mode=not args.send)
        result = await service.generate_and_dispatch()
        
        print("\n" + "="*50)
        print(" УТРЕННИЙ ПУЛЬС РОПА (ПРЕДПРОСМОТР)")
        print("="*50 + "\n")
        
        # Убираем HTML-теги для красивого отображения в консоли
        raw_text = result["telegram_html"]
        clean_text = (
            raw_text.replace("<b>", "")
            .replace("</b>", "")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<code>", "")
            .replace("</code>", "")
            .replace("<a href='", "")
            .replace("'>", " [")
            .replace("</a>", "]")
        )
        print(clean_text)
        print("\n" + "="*50)
        print(f"Статус: {result['status']} (режим: {result['mode']})")
        print("="*50 + "\n")

    asyncio.run(_run())


if __name__ == "__main__":
    main()

