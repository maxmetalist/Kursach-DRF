from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from config.views import api_root

# Документация API
schema_view = get_schema_view(
    openapi.Info(
        title="Habit Tracker API",
        default_version="v1",
        description="API для трекера полезных привычек",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="z.max83@mail.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_root, name="api-root"),
    path("api/auth/", include("users.urls")),
    path("api/", include("habits.urls")),
    # Документация
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("swagger.json/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
