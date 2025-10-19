from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from habits.models import Habit
from habits.serializers import HabitSerializer, PublicHabitSerializer
from habits.tasks import debug_task, send_habit_reminders, send_test_reminder_default

User = get_user_model()


class HabitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")

        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Дома",
            time="08:00:00",
            action="Медитировать",
            is_pleasant=True,
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

    def test_habit_creation(self):
        """Тест создания привычки"""
        habit = Habit.objects.create(
            user=self.user,
            place="Парк",
            time="07:00:00",
            action="Бухать",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=120,
            is_public=True,
        )

        self.assertEqual(habit.action, "Бухать")
        self.assertEqual(habit.place, "Парк")
        self.assertFalse(habit.is_pleasant)
        self.assertTrue(habit.is_public)

    def test_habit_str_representation(self):
        """Тест строкового представления привычки"""
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time="09:00:00",
            action="Читать",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=90,
            is_public=False,
        )

        expected_str = f"{self.user.email}: Читать в 09:00:00 в Дом"
        self.assertEqual(str(habit), expected_str)

    def test_habit_validation_reward_and_related_habit(self):
        """Тест валидации: нельзя одновременно указывать вознаграждение и связанную привычку"""
        habit = Habit(
            user=self.user,
            place="Дом",
            time="10:00:00",
            action="Тренироваться",
            is_pleasant=False,
            related_habit=self.pleasant_habit,
            reward="Шоколадка",
            periodicity=1,
            time_to_complete=120,
            is_public=False,
        )

        with self.assertRaises(ValidationError):
            habit.clean()

    def test_habit_validation_time_to_complete(self):
        """Тест валидации времени выполнения"""
        habit = Habit(
            user=self.user,
            place="Дом",
            time="10:00:00",
            action="Тренироваться",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=121,  # Больше 120 секунд
            is_public=False,
        )

        with self.assertRaises(ValidationError):
            habit.clean()

    def test_pleasant_habit_validation(self):
        """Тест валидации приятной привычки"""
        habit = Habit(
            user=self.user,
            place="Дом",
            time="10:00:00",
            action="Слушать музыку",
            is_pleasant=True,
            reward="Не должно быть",  # Не должно быть вознаграждения
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

        with self.assertRaises(ValidationError):
            habit.clean()

    def test_related_habit_must_be_pleasant(self):
        """Тест что связанная привычка должна быть приятной"""
        useful_habit = Habit.objects.create(
            user=self.user,
            place="Спортзал",
            time="18:00:00",
            action="Тренироваться",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=120,
            is_public=False,
        )

        habit = Habit(
            user=self.user,
            place="Дом",
            time="19:00:00",
            action="Отдыхать",
            is_pleasant=False,
            related_habit=useful_habit,  # Связанная привычка не приятная
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

        with self.assertRaises(ValidationError):
            habit.clean()


class HabitSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")  # ДОБАВЬТЕ email

        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Дома",
            time="08:00:00",
            action="Поцеловать лисичку с ушками",
            is_pleasant=True,
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

        # Создаем фабрику запросов для контекста
        self.factory = APIRequestFactory()
        self.request = self.factory.post("/")
        self.request.user = self.user

    def test_habit_serializer_create(self):
        """Тест создания привычки через сериализатор"""
        data = {
            "place": "Парк",
            "time": "07:00:00",
            "action": "Бухать и орать на весь парк",
            "is_pleasant": False,
            "periodicity": 1,
            "time_to_complete": 120,
            "is_public": True,
        }

        serializer = HabitSerializer(data=data, context={"request": type("Request", (), {"user": self.user})()})
        self.assertTrue(serializer.is_valid())

        habit = serializer.save()
        self.assertEqual(habit.user, self.user)
        self.assertEqual(habit.action, "Бухать и орать на весь парк")

    def test_habit_serializer_validation(self):
        """Тест валидации сериализатора привычки"""
        data = {
            "place": "Дом",
            "time": "10:00:00",
            "action": "Тренироваться",
            "is_pleasant": False,
            "related_habit": self.pleasant_habit.id,
            "reward": "Шоколадка",  # Нельзя одновременно
            "periodicity": 1,
            "time_to_complete": 120,
            "is_public": False,
        }

        serializer = HabitSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_public_habit_serializer(self):
        """Тест сериализатора публичных привычек"""
        habit = Habit.objects.create(
            user=self.user,
            place="Библиотека",
            time="15:00:00",
            action="Громко слушать Judas Priest и класть на мнение всех",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=90,
            is_public=True,
        )

        serializer = PublicHabitSerializer(instance=habit)
        data = serializer.data

        self.assertEqual(data["action"], "Громко слушать Judas Priest и класть на мнение всех")
        self.assertEqual(data["user"], self.user.email)
        self.assertIn("place", data)
        self.assertNotIn("reward", data)  # Не должно быть в публичном сериализаторе


class HabitViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.other_user = User.objects.create_user(email="other@example.com", password="testpass123")

        self.habit = Habit.objects.create(
            user=self.user,
            place="Парк",
            time="07:00:00",
            action="Бухать",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=120,
            is_public=True,
        )

        self.private_habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time="20:00:00",
            action="Орать караоке",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=90,
            is_public=False,
        )

        self.other_user_habit = Habit.objects.create(
            user=self.other_user,
            place="Спортзал",
            time="18:00:00",
            action="Приставать к красивым девчонкам",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=120,
            is_public=False,
        )

        self.habits_list_url = reverse("habit-list-create")
        self.habit_detail_url = reverse("habit-detail", kwargs={"pk": self.habit.id})
        self.public_habits_url = reverse("public-habits")

    def test_habit_list_authenticated(self):
        """Тест получения списка привычек аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.habits_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)  # Только привычки текущего пользователя

    def test_habit_list_unauthenticated(self):
        """Тест получения списка привычек без аутентификации"""
        response = self.client.get(self.habits_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_habit_create(self):
        """Тест создания привычки"""
        self.client.force_authenticate(user=self.user)

        data = {
            "place": "Библиотека",
            "time": "15:00:00",
            "action": "Спать",
            "is_pleasant": False,
            "periodicity": 1,
            "time_to_complete": 120,
            "is_public": True,
        }

        response = self.client.post(self.habits_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 4)
        self.assertEqual(Habit.objects.last().action, "Спать")

    def test_habit_detail_owner(self):
        """Тест получения деталей привычки владельцем"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.habit_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Бухать")

    def test_habit_detail_other_user(self):
        """Тест получения деталей чужой привычки"""
        self.client.force_authenticate(user=self.other_user)

        other_habit_url = reverse("habit-detail", kwargs={"pk": self.other_user_habit.id})
        response = self.client.get(other_habit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_habits_list(self):
        """Тест получения списка публичных привычек"""
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.public_habits_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должна быть только одна публичная привычка
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["action"], "Бухать")

    def test_habit_update_owner(self):
        """Тест обновления привычки владельцем"""
        self.client.force_authenticate(user=self.user)

        data = {"action": "Бухать, как не в себя"}
        response = self.client.patch(self.habit_detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.action, "Бухать, как не в себя")

    def test_habit_delete_owner(self):
        """Тест удаления привычки владельцем"""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.habit_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 2)


class CeleryTasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", telegram_chat_id="123456"
        )

        # Создаем привычку
        now = timezone.now()
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=now.time(),
            action="Орать караоке",
            is_pleasant=False,
            periodicity=1,
            time_to_complete=60,
            is_public=False,
        )

    @patch("habits.tasks.bot_instance.send_reminder")
    def test_send_habit_reminders(self, mock_send_reminder):
        """Тест задачи отправки напоминаний"""
        mock_send_reminder.return_value = AsyncMock(return_value=True)

        result = send_habit_reminders()

        self.assertIn("Sent", result)
        self.assertTrue(mock_send_reminder.called)

    @patch("habits.tasks.send_test_reminder.delay")
    def test_send_test_reminder_default(self, mock_send_reminder):
        """Тест тестовой задачи отправки напоминаний"""
        mock_send_reminder.return_value = None

        result = send_test_reminder_default()

        self.assertIn("queued", result)
        self.assertTrue(mock_send_reminder.called)

    def test_debug_task(self):
        """Тест отладочной задачи"""
        result = debug_task()
        self.assertEqual(result, "Celery is working!")

    @patch("habits.tasks.bot_instance.send_reminder")
    def test_send_habit_reminders_no_telegram(self, mock_send_reminder):
        """Тест отправки напоминаний пользователю без Telegram"""
        self.user.telegram_chat_id = ""
        self.user.save()

        result = send_habit_reminders()

        self.assertIn("Sent 0 reminders", result)
        mock_send_reminder.assert_not_called()
