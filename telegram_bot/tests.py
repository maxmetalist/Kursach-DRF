from datetime import time
from unittest.mock import AsyncMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from habits.models import Habit
from telegram_bot.bot import HabitTrackerBot


class TelegramBotTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(8, 0, 0),
            action="Орать караоке",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

    @patch("telegram_bot.bot.Bot")
    def test_bot_initialization(self, mock_bot_class):
        """Тест инициализации бота"""
        bot = HabitTrackerBot()

        self.assertIsNotNone(bot)
        mock_bot_class.assert_called()

    @patch("telegram_bot.bot.Bot")
    async def test_send_reminder(self, mock_bot_class):
        """Тест отправки напоминания"""
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        mock_bot.send_message = AsyncMock()

        bot = HabitTrackerBot()
        bot.bot = mock_bot

        result = await bot.send_reminder("123456", self.habit)

        self.assertTrue(result)
        mock_bot.send_message.assert_called_once()

    @patch("telegram_bot.bot.Bot")
    async def test_send_reminder_failure(self, mock_bot_class):
        """Тест неудачной отправки напоминания"""
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot

        from telegram.error import TelegramError

        mock_bot.send_message = AsyncMock(side_effect=TelegramError("Telegram error"))

        bot = HabitTrackerBot()
        bot.bot = mock_bot

        result = await bot.send_reminder("123456", self.habit)

        self.assertFalse(result)

    def test_format_reminder_message(self):
        """Тест форматирования сообщения напоминания"""
        bot = HabitTrackerBot()

        message = bot._format_reminder_message(self.habit)

        self.assertIn("Орать караоке", message)
        self.assertIn("Дом", message)
        self.assertIn("08:00", message)
