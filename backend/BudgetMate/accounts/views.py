# Built-in
from typing import TYPE_CHECKING

# Django
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

# Local
from .serializers import ProfileSerializer, UserSerializer

if TYPE_CHECKING:
    # Application
    from accounts.models import User
else:
    User = get_user_model()


@login_required(login_url="core:login")
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


class ProfileViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        return User.objects.filter(user=user)  # type: ignore

    def list(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put", "patch"],
        url_path="settings",
        serializer_class=ProfileSerializer,
    )
    def settings_(self, request: Request) -> HttpResponse:
        user = request.user
        profile = user.profile  # type: ignore

        if request.method == "PATCH":
            partial = True
        else:
            partial = False

        serializer = ProfileSerializer(
            profile, data=request.data, partial=partial
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)
