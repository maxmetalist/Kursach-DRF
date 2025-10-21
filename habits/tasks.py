import asyncio
import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from habits.models import Habit
from telegram_bot.bot import bot_instance

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task
def send_habit_reminders():
    """Отправка напоминаний о привычках"""
    try:
        logger.info("Starting habit reminders task")

        now = timezone.now()
        current_time = now.time()

        # Получаем привычки для текущего времени
        habits = Habit.objects.filter(time__hour=current_time.hour, time__minute=current_time.minute)

        sent_count = 0
        for habit in habits:
            if should_send_reminder(habit):
                if habit.user.telegram_chat_id:

                    # Запускаем асинхронную задачу
                    try:
                        # Создаем новую event loop для асинхронного вызова
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        success = loop.run_until_complete(
                            bot_instance.send_reminder(habit.user.telegram_chat_id, habit)
                        )
                        loop.close()

                        if success:
                            sent_count += 1
                            logger.info(f"Sent reminder for habit: {habit.action}")

                    except Exception as e:
                        logger.error(f"Failed to send reminder for habit {habit.id}: {e}")

        logger.info(f"Completed habit reminders task. Sent {sent_count} reminders")
        return f"Sent {sent_count} reminders"

    except Exception as e:
        logger.error(f"Habit reminders task failed: {e}")
        return f"Task failed: {e}"


@shared_task
def send_daily_reminders():
    """Ежедневное напоминание о предстоящих привычках"""
    try:
        logger.info("Starting daily reminders task")

        # Получаем всех пользователей с привычками
        users_with_habits = User.objects.filter(habits__isnull=False).distinct()

        sent_count = 0
        for user in users_with_habits:
            if user.telegram_chat_id:
                habits_today = Habit.objects.filter(user=user).order_by("time")

                if habits_today.exists():
                    message = format_daily_reminder(habits_today)

                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        success = loop.run_until_complete(send_telegram_message(user.telegram_chat_id, message))
                        loop.close()

                        if success:
                            sent_count += 1

                    except Exception as e:
                        logger.error(f"Failed to send daily reminder to {user.email}: {e}")

        logger.info(f"Completed daily reminders task. Sent {sent_count} reminders")
        return f"Sent {sent_count} daily reminders"

    except Exception as e:
        logger.error(f"Daily reminders task failed: {e}")
        return f"Daily task failed: {e}"


@shared_task
def send_test_reminder(chat_id: str, habit_id: int):
    """Тестовая задача для отправки напоминания"""
    try:
        habit = Habit.objects.get(id=habit_id)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        success = loop.run_until_complete(bot_instance.send_reminder(chat_id, habit))
        loop.close()

        return f"Test reminder {'sent' if success else 'failed'}"

    except Habit.DoesNotExist:
        return "Habit not found"
    except Exception as e:
        return f"Test task failed: {e}"


@shared_task
def send_test_reminder_default():
    """Тестовая задача без аргументов для админки"""
    try:
        user_with_telegram = User.objects.filter(telegram_chat_id__isnull=False).exclude(telegram_chat_id="").first()

        if user_with_telegram and Habit.objects.filter(user=user_with_telegram).exists():
            habit = Habit.objects.filter(user=user_with_telegram).first()

            # Запускаем задачу с аргументами
            send_test_reminder.delay(user_with_telegram.telegram_chat_id, habit.id)
            return f"Test task queued for {user_with_telegram.email}"
        return "No users with Telegram found"

    except Exception as e:
        return f"Test task failed: {e}"


@shared_task
def debug_task():
    """Задача для отладки Celery"""
    logger.info("Debug task executed successfully")
    return "Celery is working!"


# Вспомогательные функции
def should_send_reminder(habit):
    """Проверить, нужно ли отправлять напоминание"""
    # Для ежедневных привычек - всегда отправляем
    if habit.periodicity == 1:
        return True

    # Для периодических привычек проверяем день
    days_since_creation = (timezone.now() - habit.created_at).days
    return days_since_creation % habit.periodicity == 0


def format_daily_reminder(habits):
    """Форматировать ежедневное напоминание"""
    message = "📅 <b>Ваши привычки на сегодня:</b>\n\n"

    for i, habit in enumerate(habits, 1):
        message += f"{i}. {habit.action} в {habit.time.strftime('%H:%M')} - {habit.place}\n"

    message += "\n💪 Удачи в выполнении привычек!"
    return message


async def send_telegram_message(chat_id, message):
    """Отправить сообщение в Telegram"""
    if not bot_instance.bot:
        logger.error("Telegram bot not configured")
        return False

    try:
        await bot_instance.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
