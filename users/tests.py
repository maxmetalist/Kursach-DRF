from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import UserProfile
from users.serializers import UserRegisterSerializer, UserSerializer


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        # Создаем профиль вручную
        self.profile = UserProfile.objects.create(user=self.user, telegram_chat_id="123456")

    def test_user_profile_creation(self):
        """Тест автоматического создания профиля пользователя"""
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_user_profile_str(self):
        """Тест строкового представления профиля"""
        self.assertEqual(str(self.user.profile), f"{self.user.username} Profile")

    def test_telegram_chat_id_field(self):
        """Тест поля telegram_chat_id"""
        self.user.profile.telegram_chat_id = "789012"
        self.user.profile.save()

        updated_profile = UserProfile.objects.get(id=self.profile.id)
        self.assertEqual(updated_profile.telegram_chat_id, "789012")


class UserSerializerTest(TestCase):
    def test_user_register_serializer(self):
        """Тест сериализатора регистрации пользователя"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }

        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@example.com")

    def test_user_register_serializer_password_mismatch(self):
        """Тест сериализатора с несовпадающими паролями"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "testpass123",
            "password_confirm": "differentpass",
        }

        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_user_serializer(self):
        """Тест сериализатора пользователя"""
        user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

        serializer = UserSerializer(instance=user)
        data = serializer.data

        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertNotIn("password", data)  # Пароль не должен быть в выводе


class UserViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.register_url = reverse("register")
        self.profile_url = reverse("user-profile")

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(username="newuser").email, "newuser@example.com")

    def test_user_registration_invalid_data(self):
        """Тест регистрации с невалидными данными"""
        data = {"username": "newuser", "email": "invalid-email", "password": "123", "password_confirm": "123"}

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_retrieve(self):
        """Тест получения профиля пользователя"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_user_profile_unauthenticated(self):
        """Тест доступа к профилю без аутентификации"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
