"""
URL configuration for the api.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from users.views import ExampleUserLookup

from . import views as api_views

urlpatterns = [
    #
    # General
    #
    path("", api_views.index),
    path("robots.txt", api_views.robots),
    path("favicon.ico", api_views.favicon),
    path("health", api_views.health),
    path("admin", admin.site.urls),
    #
    # API docs
    #
    path("docs", SpectacularSwaggerView.as_view(url_name="schema")),
    path("docs/schema", SpectacularAPIView.as_view(), name="schema"),
    #
    # Auth
    #
    path("users/<int:user_id>", ExampleUserLookup.as_view(), name="user_lookup"),
]
