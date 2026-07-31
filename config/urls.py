from django.conf import settings
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.general.views import HealthView, IndexView

handler404 = "apps.general.views.page_not_found"

urlpatterns = [
    # Admin
    path(settings.ADMIN_URL, admin.site.urls),
    # General
    path("", IndexView.as_view(), name="index"),
    path("health", HealthView.as_view(), name="health"),
    # Docs
    path("schema", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "docs",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]
