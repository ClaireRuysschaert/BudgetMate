# Built-in
from typing import TYPE_CHECKING, Dict, Type

# Django
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Application
from accounts.models import Profile

if TYPE_CHECKING:
    # Application
    from accounts.models import User
else:
    User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender: Type[User], instance: User, created: bool, **kwargs: Dict) -> None:
    if created:
        Profile.objects.create(user=instance)
