from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

User = get_user_model()


class UserPrivateViewSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "created_at", "updated_at"]


class UserPublicViewSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "created_at", "updated_at"]
