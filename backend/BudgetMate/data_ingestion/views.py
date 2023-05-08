from rest_framework import generics
from rest_framework.response import Response


class UploadFileView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        # Show content of csv file
        print(request.data['file'].read().decode('utf-8'))
        return Response({'message': 'POST: Received a file!'})
