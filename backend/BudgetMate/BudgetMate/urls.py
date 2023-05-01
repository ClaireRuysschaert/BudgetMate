"""BudgetMate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers

import accounts.views as accounts_views

# Local
from .urls_api import router as api_router

router = routers.DefaultRouter()
router.registry.extend(api_router.registry)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    re_path("", include("accounts.urls", namespace="core")),
    # Match all and forward to react router on the front-end app.
    re_path(r"^(?:.*)/?$", accounts_views.index),
]

if settings.DEBUG:
    # Third-party
    import debug_toolbar

    urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
