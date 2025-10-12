from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        "message": "Habit Tracker API",
        "endpoints": {
            "auth": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "token_refresh": "/api/auth/token/refresh/",
                "profile": "/api/auth/profile/",
            },
            "habits": {
                "my_habits": "/api/habits/",
                "public_habits": "/api/habits/public/",
            },
            "documentation": {
                "swagger": "/swagger/",
                "redoc": "/redoc/",
            }
        }
    })
