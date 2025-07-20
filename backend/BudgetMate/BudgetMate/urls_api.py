from django.urls import path
from rest_framework import routers

from data_ingestion.views import UploadFileView

router = routers.DefaultRouter()

urlpatterns = [
    # Data Ingestion
    path("upload/", UploadFileView.as_view(), name="upload"),
]
