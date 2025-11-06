# tenabot/tenabot/views.py
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import login
from .utils import check_telegram_data_integrity
from users.models import User
from users.serializers import UserSerializer
import urllib.parse
from rest_framework import status
from django.middleware.csrf import get_token
import json

@api_view(["POST"])
@permission_classes([AllowAny])
@ensure_csrf_cookie   # <-- ensures csrftoken cookie is set on response
def register_telegram_user(request):
    data = request.data

    init_data = data.get("initData")
    if not init_data or not check_telegram_data_integrity(init_data):
        return Response({"success": False, "detail": "Invalid Telegram data signature."},
                        status=status.HTTP_403_FORBIDDEN)

    # parse init_data into dict
    try:
        init_data_dict = dict(urllib.parse.parse_qsl(init_data))
        user_json = init_data_dict.get('user') or init_data_dict.get('sender')
        if not user_json:
            return Response({"success": False, "detail": "User data missing from initData."},
                            status=status.HTTP_400_BAD_REQUEST)
        telegram_user_data = json.loads(urllib.parse.unquote(user_json))
        telegram_id = str(telegram_user_data.get("id"))
    except Exception:
        return Response({"success": False, "detail": "Failed to parse Telegram user data."},
                        status=status.HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": telegram_user_data.get("username") or f"user_{telegram_id}",
            "first_name": telegram_user_data.get("first_name", ""),
            "last_name": telegram_user_data.get("last_name", ""),
            "avatar_url": telegram_user_data.get("photo_url", None),
        },
    )

    if not created:
        user.username = telegram_user_data.get("username", user.username)
        user.first_name = telegram_user_data.get("first_name", user.first_name)
        user.last_name = telegram_user_data.get("last_name", user.last_name)
        user.avatar_url = telegram_user_data.get("photo_url", user.avatar_url)
        user.save()

    # Create session for the user
    login(request, user)

    serializer = UserSerializer(user)
    csrf_token = get_token(request)

    return Response({
        "success": True,
        "user": serializer.data,
        "csrf_token": csrf_token,
    }, status=status.HTTP_200_OK)
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response

# from users.serializers import UserSerializer


# from django.contrib.auth import get_user_model


# User = get_user_model()
# @api_view(["POST"])
# @permission_classes([AllowAny])
# def register_telegram_user(request):
#     data = request.data
#     telegram_id = data.get("telegram_id")

#     user, created = User.objects.get_or_create(
#         telegram_id=telegram_id,
#         defaults={
#             "username": data.get("username") or f"user_{telegram_id}",
#             "first_name": data.get("first_name", ""),
#             "last_name": data.get("last_name", ""),
#             "avatar_url": data.get("avatar_url", None),
#         },
#     )
#     if not created:
#         # Optionally update user info
#         user.username = data.get("username", user.username)
#         user.first_name = data.get("first_name", user.first_name)
#         user.last_name = data.get("last_name", user.last_name)
#         user.avatar_url = data.get("avatar_url", user.avatar_url)
#         user.save()

#     serializer = UserSerializer(user)
#     return Response({"success": True, "user": serializer.data})

   
    
# @api_view(["GET"])
# @permission_classes([AllowAny])
# def get_user(request, telegram_id):
#     try:
#         user = User.objects.get(telegram_id=telegram_id)
#         serializer = UserSerializer(user)
#         return Response({"success": True, "user": serializer.data})
#     except User.DoesNotExist:
#         return Response({"success": False, "error": "User not found"}, status=404) 
# @api_view(["GET"])
# @permission_classes([AllowAny])
# def get_users(request):
#     try:
#         users = User.objects.all()
#         serializer = UserSerializer(users,many=True)
#         return Response({"success": True, "user": serializer.data})
#     except User.DoesNotExist:
#         return Response({"success": False, "error": "User not found"}, status=404)














