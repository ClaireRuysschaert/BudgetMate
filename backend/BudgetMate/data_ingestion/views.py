from rest_framework import viewsets
from rest_framework.response import Response


class DummyViewSet(viewsets.ViewSet):
    """
    A dummy viewset to test the API
    """
    def list(self, request):
        """
        Returns a dummy response
        """
        return Response({'message': 'Hello World!'})
