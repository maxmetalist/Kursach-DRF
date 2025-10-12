import logging
import os

import django
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError

from habits.models import Habit

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HabitTrackerBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token or self.token == "your-telegram-bot-token-here":
            logger.warning("Telegram bot token not set. Please set TELEGRAM_BOT_TOKEN in settings.")
            self.bot = None
        else:
            self.bot = Bot(token=self.token)
        self._me = None

    async def get_me(self):
        """Получить информацию о боте"""
        if not self.bot:
            raise ValueError("Telegram bot token not configured")
        if not self._me:
            self._me = await self.bot.get_me()
        return self._me

    async def send_reminder(self, chat_id: str, habit: Habit):
        """Отправить напоминание о привычке"""
        if not self.bot:
            logger.error("Cannot send reminder: Telegram bot not configured")
            return False

        try:
            message = self._format_reminder_message(habit)
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            logger.info(f"Reminder sent to {chat_id} for habit: {habit.action}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send reminder to {chat_id}: {e}")
            return False

    def _format_reminder_message(self, habit: Habit) -> str:
        """Форматирование сообщения напоминания"""
        message = (
            f"🔔 <b>Напоминание о привычке!</b>\n\n"
            f"📝 <b>Действие:</b> {habit.action}\n"
            f"📍 <b>Место:</b> {habit.place}\n"
            f"⏰ <b>Время:</b> {habit.time.strftime('%H:%M')}\n"
            f"⏱️ <b>Время на выполнение:</b> {habit.time_to_complete} сек.\n"
        )

        if habit.reward:
            message += f"🎁 <b>Вознаграждение:</b> {habit.reward}\n"
        elif habit.related_habit:
            message += f"😊 <b>Приятная привычка:</b> {habit.related_habit.action}\n"

        message += "\n💪 Удачи в выполнении!"
        return message

    async def send_welcome_message(self, chat_id: str):
        """Отправить приветственное сообщение"""
        if not self.bot:
            logger.error("Cannot send welcome message: Telegram bot not configured")
            return False

        welcome_text = """
            👋 <b>Здорово! Это Трекер Привычек!</b>
            Я те буду постоянно напоминать о привычках в нужное время и доставать этим.
            Чтобы начать получать напоминания:
            1. Надо зарегаться на сайте
            2. Добавить свои привычки
            3. И главное, укажи свой Telegram ID в профиле
            Ну что, погнали! 🚀
            """

        try:
            await self.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send welcome message to {chat_id}: {e}")
            return False


# Глобальный экземпляр бота
bot_instance = HabitTrackerBot()
