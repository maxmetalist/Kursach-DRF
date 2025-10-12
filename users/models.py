from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    telegram_chat_id = models.CharField(
        max_length=100, blank=True, null=True, unique=True, verbose_name="Telegram Chat ID"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name="Telegram username")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} Profile"
