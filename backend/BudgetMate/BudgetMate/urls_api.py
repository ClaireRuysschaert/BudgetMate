from rest_framework import routers

from data_ingestion.views import DummyViewSet

router = routers.DefaultRouter()

# Data Ingestion
router.register('dummy', DummyViewSet, basename='dummy')
