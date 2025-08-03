from django.contrib.auth import get_user_model
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserPublicViewSerializer

User = get_user_model()


# Add your auth endpoints here.
# Use patterns from here: https://www.django-rest-framework.org/api-guide/authentication/
# dj-rest-auth and django-rest-knox are very good packages I suggest


class ExampleUserLookup(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Lookup a user by ID",
        description="""
        It retrieves the details of a user based on the provided user ID.
        """,
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="The ID of the user to look up.",
                required=True,
            ),
        ],
        responses={
            status.HTTP_200_OK: UserPublicViewSerializer,
            status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        },
    )
    def get(self, request, user_id: int):
        """Example endpoint for looking up users by id"""

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404("User id not found")

        return Response(UserPublicViewSerializer(user).data, status=status.HTTP_200_OK)
