from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from habits.models import Habit
from habits.pagination import HabitPagination
from habits.permissions import IsOwner
from habits.serializers import HabitSerializer, PublicHabitSerializer


class HabitListCreateView(generics.ListCreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    pagination_class = HabitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_pleasant", "is_public", "periodicity"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Habit.objects.none()
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Habit.objects.none()
        return Habit.objects.filter(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    serializer_class = PublicHabitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HabitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["periodicity"]

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)
