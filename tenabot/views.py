

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import login
from .utils import check_telegram_data_integrity # Import the function above
from users.models import User # Your custom user model
from users.serializers import UserSerializer
import urllib.parse
from rest_framework import status

@api_view(["POST"])
@permission_classes([AllowAny])
def register_telegram_user(request):
    data = request.data
    
    # --- 1. Security Check ---
    init_data = data.get("initData")
    if not check_telegram_data_integrity(init_data):
        return Response(
            {"success": False, "detail": "Invalid Telegram data signature."}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # --- 2. Extract Telegram ID from safe data ---
    # We must use the data from initData, which we just verified.
    # The user object is nested and URL-encoded within initData.
    try:
        init_data_dict = dict(urllib.parse.parse_qsl(init_data))
        user_json = init_data_dict.get('user') or init_data_dict.get('sender')
        if not user_json:
            return Response({"success": False, "detail": "User data missing from initData."}, status=status.HTTP_400_BAD_REQUEST)
        
        # We need to manually parse the 'user' JSON string inside initData
        import json
        telegram_user_data = json.loads(urllib.parse.unquote(user_json))
        telegram_id = str(telegram_user_data.get("id")) # Ensure it's a string

    except Exception:
        return Response({"success": False, "detail": "Failed to parse Telegram user data."}, status=status.HTTP_400_BAD_REQUEST)

    # --- 3. Get or Create User (Using verified telegram_id) ---
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
        # Optionally update user info from the latest Telegram data
        user.username = telegram_user_data.get("username", user.username)
        user.first_name = telegram_user_data.get("first_name", user.first_name)
        user.last_name = telegram_user_data.get("last_name", user.last_name)
        user.avatar_url = telegram_user_data.get("photo_url", user.avatar_url)
        user.save()

    # --- 4. Log in the user (Set Session Cookie) ---
    # This creates a session for the user, essential for DRF SessionAuthentication
    login(request, user) 

    serializer = UserSerializer(user)
    return Response({"success": True, "user": serializer.data})
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














