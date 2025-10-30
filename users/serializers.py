from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar_url",
            "is_premium",
            "created_at",
        ]
