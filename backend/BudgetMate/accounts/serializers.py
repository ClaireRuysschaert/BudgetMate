# Django
from django.contrib.auth import get_user_model
from rest_framework import serializers

# Local
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = [
            "email",
            "first_name",
            "last_name",
            "profile",
        ]
