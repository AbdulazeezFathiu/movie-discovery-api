from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)

from .serializers import RegisterSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        responses=inline_serializer(
            name="UserProfileResponse",
            fields={
                "id": serializers.IntegerField(),
                "username": serializers.CharField(),
                "email": serializers.EmailField(),
            },
        )
    )
)
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })