# Django
from django.conf.urls import include
from django.contrib.auth.views import LoginView
from django.urls import path

app_name = "core"
urlpatterns = [
    path(
        "accounts/login/",
        LoginView.as_view(),
        name="login",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]
