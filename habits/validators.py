from django.core.exceptions import ValidationError


def validate_habit(habit):
    """Централизованный валидатор для модели Habit"""

    # Валидация 1: нельзя одновременно указывать связанную привычку и вознаграждение
    if habit.related_habit and habit.reward:
        raise ValidationError(
            "Ну чел, нельзя два раза награждать себя за одно и то же."
            "Не будь самым хитроухим. Сначала полезное, потом приятное."
        )

    # Валидация 2: время выполнения не больше 120 секунд
    if habit.time_to_complete > 120:
        raise ValidationError(
            "А время-то тик-так.Есть всего 120 секунд на выполнение."
            "Забываешь отметить? Ну, не запостил,- не было..."
        )

    # Валидация 3: в связанные привычки могут попадать только приятные привычки
    if habit.related_habit and not habit.related_habit.is_pleasant:
        raise ValidationError(
            "Аскетизм, конечно, хорошо, но в связанные привычки кидаем только приятные."
            "Они же, типа, награда. Вот и побалуй себя."
        )

    # Валидация 4: у приятной привычки не может быть вознаграждения или связанной привычки
    if habit.is_pleasant:
        if habit.reward or habit.related_habit:
            raise ValidationError(
                "Ты вот реально хочешь награду за награду?"
                "Да уж! Я смотрю борзометр у тебя совсем отключен."
                "Одна полезная,- одна приятная. Только так!"
            )

    # Валидация 5: периодичность от 1 до 7 дней
    if habit.periodicity < 1 or habit.periodicity > 7:
        raise ValidationError("Периодичность должна быть от 1 до 7 дней.")
