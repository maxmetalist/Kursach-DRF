import logging

from django.core.management.base import BaseCommand

from habits.models import Habit
from habits.tasks import send_habit_reminders
from users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send habit reminders via Telegram"

    def add_arguments(self, parser):
        parser.add_argument("--test", action="store_true", help="Test mode - send to first available user")
        parser.add_argument("--async", action="store_true", help="Send as async Celery task")

    def handle(self, *args, **options):
        self.stdout.write("Sending habit reminders...")

        try:
            if options["test"]:
                if options["async"]:
                    result = self.send_test_reminder_async()
                else:
                    result = self.send_test_reminder_sync()
            else:
                if options["async"]:
                    result = send_habit_reminders.delay()
                    self.stdout.write(f"Task queued: {result.id}")
                else:
                    result = send_habit_reminders()

            self.stdout.write(self.style.SUCCESS(f"Success: {result}"))
        except Exception as e:
            logger.error(f"Failed to send reminders: {e}")
            self.stdout.write(self.style.ERROR(f"Failed to send reminders: {e}"))

    def send_test_reminder_async(self):
        """Отправить тестовое напоминание асинхронно"""
        profile = User.objects.filter(telegram_chat_id__isnull=False).first()

        if profile and Habit.objects.filter(user=profile.user).exists():
            habit = Habit.objects.filter(user=profile.user).first()
            return self.send_test_reminder.delay(profile.telegram_chat_id, habit.id)
        return "No users with Telegram found"

    def send_test_reminder_sync(self):
        """Отправить тестовое напоминание синхронно"""
        import asyncio

        from telegram_bot.bot import bot_instance

        profile = User.objects.filter(telegram_chat_id__isnull=False).first()

        if profile and Habit.objects.filter(user=profile.user).exists():
            habit = Habit.objects.filter(user=profile.user).first()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success = loop.run_until_complete(bot_instance.send_reminder(profile.telegram_chat_id, habit))
            loop.close()

            return "Test reminder sent" if success else "Test reminder failed"
        return "No users with Telegram found"
