from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.serializers import UserRegisterSerializer, UserSerializer

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))

    def test_user_str_representation(self):
        """Тест строкового представления пользователя"""
        self.assertEqual(str(self.user), "test@example.com")

    def test_telegram_fields(self):
        """Тест полей Telegram"""
        self.user.telegram_chat_id = "123456"
        self.user.telegram_username = "testuser"
        self.user.save()

        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.telegram_chat_id, "123456")
        self.assertEqual(updated_user.telegram_username, "testuser")


class UserSerializerTest(TestCase):
    def test_user_register_serializer(self):
        """Тест сериализатора регистрации пользователя"""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }

        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertIsNone(user.username)  # username должен быть None

    def test_user_register_serializer_password_mismatch(self):
        """Тест сериализатора с несовпадающими паролями"""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "password_confirm": "differentpass",
        }

        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_user_serializer(self):
        """Тест сериализатора пользователя"""
        user = User.objects.create_user(email="test@example.com", password="testpass123")

        serializer = UserSerializer(instance=user)
        data = serializer.data

        self.assertEqual(data["email"], "test@example.com")
        self.assertNotIn("password", data)  # Пароль не должен быть в выводе


class UserViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.register_url = reverse("register")
        self.profile_url = reverse("user-profile")

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(email="newuser@example.com").email, "newuser@example.com")

    def test_user_registration_invalid_data(self):
        """Тест регистрации с невалидными данными"""
        data = {"email": "invalid-email", "password": "123", "password_confirm": "123"}

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_retrieve(self):
        """Тест получения профиля пользователя"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_user_profile_unauthenticated(self):
        """Тест доступа к профилю без аутентификации"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
