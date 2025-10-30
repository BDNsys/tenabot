

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import User
from users.serializers import UserSerializer

@api_view(["POST"])
@permission_classes([AllowAny])
def register_telegram_user(request):
    data = request.data
    telegram_id = data.get("telegram_id")

    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": data.get("username") or f"user_{telegram_id}",
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "avatar_url": data.get("avatar_url", None),
        },
    )
    if not created:
        # Optionally update user info
        user.username = data.get("username", user.username)
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.avatar_url = data.get("avatar_url", user.avatar_url)
        user.save()

    serializer = UserSerializer(user)
    return Response({"success": True, "user": serializer.data})

   
    
@api_view(["GET"])
@permission_classes([AllowAny])
def get_user(request, telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        serializer = UserSerializer(user)
        return Response({"success": True, "user": serializer.data})
    except User.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)
    
@api_view(["GET"])
@permission_classes([AllowAny])
def get_users(request):
    try:
        users = User.objects.all()
        serializer = UserSerializer(users)
        return Response({"success": True, "user": serializer.data})
    except User.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)














