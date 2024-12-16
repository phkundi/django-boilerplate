from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


class DeleteUserView(APIView):
    def delete(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
