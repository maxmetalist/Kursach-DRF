from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Habit(models.Model):
    PERIODICITY_CHOICES = [
        (1, "Ежедневно"),
        (2, "Раз в 2 дня"),
        (3, "Раз в 3 дня"),
        (4, "Раз в 4 дня"),
        (5, "Раз в 5 дней"),
        (6, "Раз в 6 дней"),
        (7, "Еженедельно"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    place = models.CharField(max_length=255, verbose_name="Место")
    time = models.TimeField(verbose_name="Время")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(default=False, verbose_name="Признак приятной привычки")
    related_habit = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанная привычка"
    )
    periodicity = models.PositiveIntegerField(choices=PERIODICITY_CHOICES, default=1, verbose_name="Периодичность")
    reward = models.CharField(max_length=255, blank=True, verbose_name="Вознаграждение")
    time_to_complete = models.PositiveIntegerField(
        verbose_name="Время на выполнение (в секундах)", validators=[MinValueValidator(1), MaxValueValidator(120)]
    )
    is_public = models.BooleanField(default=False, verbose_name="Признак публичности")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-created_at"]

    def clean(self):
        from .validators import validate_habit

        # Используем централизованный валидатор
        validate_habit(self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.action} в {self.time} в {self.place}"
