from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.permissions import IsOwner
from users.serializers import UserRegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_telegram(request):
    """Связать Telegram аккаунт с профилем пользователя"""
    telegram_chat_id = request.data.get('telegram_chat_id')
    telegram_username = request.data.get('telegram_username')

    if not telegram_chat_id:
        return Response(
            {"error": "telegram_chat_id обязателен"},
            status=status.HTTP_400_BAD_REQUEST
        )

    profile = request.user.profile
    profile.telegram_chat_id = telegram_chat_id
    if telegram_username:
        profile.telegram_username = telegram_username
    profile.save()

    return Response({
        "message": "Telegram аккаунт успешно привязан",
        "telegram_chat_id": profile.telegram_chat_id,
        "telegram_username": profile.telegram_username
    })
