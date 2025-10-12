from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit
from habits.validators import validate_habit


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "periodicity",
            "reward",
            "time_to_complete",
            "is_public",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        # Создаем временный объект для валидации
        habit = Habit(**data)
        if self.instance:
            habit.id = self.instance.id

        # Используем централизованный валидатор
        try:
            validate_habit(habit)
        except ValidationError as e:
            raise serializers.ValidationError(e.message)

        return data


class PublicHabitSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = Habit
        fields = ["id", "user", "place", "time", "action", "periodicity", "time_to_complete", "created_at"]
        read_only_fields = fields
