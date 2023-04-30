# Django
from django.contrib.auth import get_user_model
from django.test import TestCase

# Application
from accounts.models import Profile

User = get_user_model()


class TestUserProfile(TestCase):
    def test_signal_create_profile(self):
        user = User.objects.create_user(
            username="usertest1", password="5tr0ngP@ssw0rd!!"
        )
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(user.profile, Profile.objects.get())
