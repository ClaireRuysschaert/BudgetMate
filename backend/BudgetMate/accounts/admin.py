# Django
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


class UserModelAdmin(UserAdmin):
    inlines = UserAdmin.inlines


admin.site.register(get_user_model(), UserAdmin)
