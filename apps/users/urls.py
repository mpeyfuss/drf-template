from django.urls import path

from apps.users.views import CsrfView

app_name = "users"

urlpatterns = [
    path("csrf", CsrfView.as_view(), name="csrf"),
]
