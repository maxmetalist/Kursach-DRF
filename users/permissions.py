from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Для User объекта
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
        # Для других объектов
        return obj == request.user

    def has_permission(self, request, view):
        # Разрешаем доступ для документации
        if getattr(view, 'swagger_fake_view', False):
            return True
        return super().has_permission(request, view)
