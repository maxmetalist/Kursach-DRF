import asyncio
import logging

from django.core.management.base import BaseCommand

from telegram_bot.bot import bot_instance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start Telegram bot for polling"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Telegram bot..."))

        try:
            asyncio.run(self.run_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bot stopped by user"))
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.stdout.write(self.style.ERROR(f"Bot error: {e}"))

    async def run_bot(self):
        """Запуск бота"""
        me = await bot_instance.get_me()
        self.stdout.write(self.style.SUCCESS(f"Bot @{me.username} started successfully!"))
