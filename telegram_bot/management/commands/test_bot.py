import asyncio

from django.core.management.base import BaseCommand

from telegram_bot.bot import bot_instance


class Command(BaseCommand):
    help = "Test Telegram bot connection"

    def handle(self, *args, **options):
        self.stdout.write("Testing Telegram bot...")

        try:
            # Тестируем подключение
            me = asyncio.run(bot_instance.get_me())
            self.stdout.write(self.style.SUCCESS(f"Bot @{me.username} is working!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Bot test failed: {e}"))
            self.stdout.write(self.style.WARNING("Make sure TELEGRAM_BOT_TOKEN is set in settings.py"))
