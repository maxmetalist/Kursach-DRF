import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_scheduler = {
    "send-habit-reminders-every-minute": {
        "task": "habits.tasks.send_habit_reminders",
        "schedule": crontab(minute="*"),  # Каждую минуту
    },
    "send-daily-reminders-at-8am": {
        "task": "habits.tasks.send_daily_reminders",
        "schedule": crontab(hour=8, minute=0),  # Каждый день в 8:00
    },
    "send-test-reminder-every-5-minutes": {
        "task": "habits.tasks.send_test_reminder_default",  # Задача без аргументов
        "schedule": crontab(minute="*/5"),  # Каждые 5 минут
    },
}

app.conf.timezone = "Europe/Moscow"
