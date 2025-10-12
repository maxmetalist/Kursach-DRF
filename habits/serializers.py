from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from habits.models import Habit


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
        instance = getattr(self, "instance", None)

        if instance:
            # Создаем копию instance с обновленными полями
            temp_instance = Habit.objects.get(pk=instance.pk)
            for attr, value in data.items():
                setattr(temp_instance, attr, value)
            habit = temp_instance
        else:
            # Для создания используем переданные данные
            habit = Habit(**data)

        # Используем централизованный валидатор
        try:
            from habits.validators import validate_habit

            validate_habit(habit)
        except ValidationError as e:
            raise serializers.ValidationError(e.message)

        return data

    def update(self, instance, validated_data):
        # Обычное обновление, но с гарантией, что time_to_complete не None
        if "time_to_complete" in validated_data and validated_data["time_to_complete"] is None:
            # Если передали None, используем текущее значение
            validated_data.pop("time_to_complete")

        return super().update(instance, validated_data)


class PublicHabitSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = Habit
        fields = ["id", "user", "place", "time", "action", "periodicity", "time_to_complete", "created_at"]
        read_only_fields = fields
