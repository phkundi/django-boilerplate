from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.emails import send_contact_notification


class ContactFormView(APIView):
    def post(self, request):
        data = request.data
        try:
            send_contact_notification(data)
            return Response({"message": "Data received"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
