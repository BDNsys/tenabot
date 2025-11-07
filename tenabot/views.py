# tenabot/tenabot/views.py
import json
import logging
import urllib.parse

from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.contrib.auth import login
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .utils import check_telegram_data_integrity
from users.models import User
from users.serializers import UserSerializer

logger = logging.getLogger(__name__)

from django.utils.decorators import method_decorator
from rest_framework.views import APIView
@method_decorator(csrf_exempt, name='dispatch')
class RegisterTelegramUser(APIView):
    permission_classes = [AllowAny]
    def post(request):
        """
        Debug-friendly version: logs request headers/body and each parsing/validation step.
        Once debugging is done, remove csrf_exempt and implement appropriate CSRF/auth handling.
        """
        try:
            # Log incoming request metadata
            logger.debug("=== register_telegram_user called ===")
            logger.debug("Remote addr: %s", request.META.get("REMOTE_ADDR"))
            logger.debug("Request method: %s", request.method)
            logger.debug("Content-Type: %s", request.META.get("CONTENT_TYPE"))
            logger.debug("Headers (subset): Authorization=%s, X-Requested-With=%s, X-Telegram-InitData=%s",
                        request.META.get("HTTP_AUTHORIZATION"),
                        request.META.get("HTTP_X_REQUESTED_WITH"),
                        request.META.get("HTTP_X_TELEGRAM_INITDATA"))
            # Log body safely: if too large, log first N bytes
            body = getattr(request, "body", b"")
            try:
                body_preview = body.decode("utf-8")[:2000]
            except Exception:
                body_preview = "<binary or non-utf8 body>"
            logger.debug("Request body preview (first 2000 chars): %s", body_preview)

            data = request.data or {}
            logger.debug("Parsed request.data: %s", data)

            # Step 1: find initData
            init_data = data.get("initData") or request.headers.get("X-Telegram-InitData") or data.get("init_data")
            logger.debug("init_data resolved to: %s", init_data if init_data else "<None>")

            if not init_data:
                logger.warning("Missing initData in request (body keys: %s). Returning 400.", list(data.keys()))
                return Response(
                    {"success": False, "detail": "Missing initData in request body or X-Telegram-InitData header."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Step 1b: run integrity check and log result
            # try:
            #     integrity_ok = check_telegram_data_integrity(init_data)
            # except Exception as e:
            #     logger.exception("check_telegram_data_integrity raised an exception: %s", e)
            #     return Response(
            #         {"success": False, "detail": "Telegram integrity check raised an exception."},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )

            # logger.debug("check_telegram_data_integrity result: %s", integrity_ok)
            # if not integrity_ok:
            #     logger.warning("Telegram data integrity check failed for initData: %s", init_data[:120])
            #     return Response({"success": False, "detail": "Invalid Telegram data signature."}, status=status.HTTP_403_FORBIDDEN)

            # Step 2: parse initData (query-string-like)
            try:
                init_data_dict = dict(urllib.parse.parse_qsl(init_data))
                logger.debug("Parsed init_data into dict with keys: %s", list(init_data_dict.keys()))
                user_json = init_data_dict.get('user') or init_data_dict.get('sender')
                if not user_json:
                    logger.warning("initData contained no 'user' or 'sender'. init_data_dict: %s", init_data_dict)
                    return Response({"success": False, "detail": "User data missing from initData."}, status=status.HTTP_400_BAD_REQUEST)

                # Telegram sometimes URL-encodes the JSON string; unquote then load
                telegram_user_data = json.loads(urllib.parse.unquote(user_json))
                logger.debug("telegram_user_data parsed: %s", telegram_user_data)
                telegram_id = str(telegram_user_data.get("id"))
                if not telegram_id:
                    logger.warning("telegram_user_data has no id field: %s", telegram_user_data)
                    return Response({"success": False, "detail": "Telegram user id missing."}, status=status.HTTP_400_BAD_REQUEST)
            except json.JSONDecodeError as e:
                logger.exception("JSON decode error parsing user field from initData: %s", e)
                return Response({"success": False, "detail": "Failed to parse Telegram user JSON."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.exception("Unexpected error parsing initData: %s", e)
                return Response({"success": False, "detail": "Failed to parse Telegram user data."}, status=status.HTTP_400_BAD_REQUEST)

            # Step 3: get or create user
            try:
                user, created = User.objects.get_or_create(
                    telegram_id=telegram_id,
                    defaults={
                        "username": telegram_user_data.get("username") or f"user_{telegram_id}",
                        "first_name": telegram_user_data.get("first_name", ""),
                        "last_name": telegram_user_data.get("last_name", ""),
                        "avatar_url": telegram_user_data.get("photo_url", None),
                    },
                )
                logger.debug("User get_or_create result: created=%s, user_id=%s, username=%s", created, user.id, user.username)
                if not created:
                    # update latest info
                    user.username = telegram_user_data.get("username", user.username)
                    user.first_name = telegram_user_data.get("first_name", user.first_name)
                    user.last_name = telegram_user_data.get("last_name", user.last_name)
                    user.avatar_url = telegram_user_data.get("photo_url", user.avatar_url)
                    user.save()
                    logger.debug("Existing user updated from Telegram data: %s", user.id)
            except Exception as e:
                logger.exception("DB error creating/updating user: %s", e)
                return Response({"success": False, "detail": "Database error creating/updating user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Step 4: login (create session)
            try:
                login(request, user)
                logger.debug("login() succeeded for user %s (id=%s)", user.username, user.id)
            except Exception as e:
                logger.exception("login() raised exception: %s", e)
                # don't expose internal error; return 500 so you can check logs
                return Response({"success": False, "detail": "Failed to create session."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            serializer = UserSerializer(user)
            csrf = get_token(request)
            logger.info("Telegram register success for user_id=%s telegram_id=%s", user.id, telegram_id)
            return Response({"success": True, "user": serializer.data, "csrf_token": csrf})

        except Exception as top_e:
            logger.exception("Unhandled exception in register_telegram_user: %s", top_e)
            return Response({"success": False, "detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# from django.views.decorators.csrf import ensure_csrf_cookie
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from django.contrib.auth import login
# from .utils import check_telegram_data_integrity
# from users.models import User
# from users.serializers import UserSerializer
# import urllib.parse
# from rest_framework import status
# from django.middleware.csrf import get_token
# import json
# from django.views.decorators.csrf import csrf_exempt
# @csrf_exempt
# @api_view(["POST"])
# @permission_classes([AllowAny])
# @ensure_csrf_cookie   # <-- ensures csrftoken cookie is set on response
# def register_telegram_user(request):
#     data = request.data

#     init_data = data.get("initData")
#     # if not init_data or not check_telegram_data_integrity(init_data):
#     #     return Response({"success": False, "detail": "Invalid Telegram data signature."},
#     #                     status=status.HTTP_403_FORBIDDEN)

#     # parse init_data into dict
#     try:
#         init_data_dict = dict(urllib.parse.parse_qsl(init_data))
#         user_json = init_data_dict.get('user') or init_data_dict.get('sender')
#         if not user_json:
#             return Response({"success": False, "detail": "User data missing from initData."},
#                             status=status.HTTP_400_BAD_REQUEST)
#         telegram_user_data = json.loads(urllib.parse.unquote(user_json))
#         telegram_id = str(telegram_user_data.get("id"))
#     except Exception:
#         return Response({"success": False, "detail": "Failed to parse Telegram user data."},
#                         status=status.HTTP_400_BAD_REQUEST)

#     user, created = User.objects.get_or_create(
#         telegram_id=telegram_id,
#         defaults={
#             "username": telegram_user_data.get("username") or f"user_{telegram_id}",
#             "first_name": telegram_user_data.get("first_name", ""),
#             "last_name": telegram_user_data.get("last_name", ""),
#             "avatar_url": telegram_user_data.get("photo_url", None),
#         },
#     )

#     if not created:
#         user.username = telegram_user_data.get("username", user.username)
#         user.first_name = telegram_user_data.get("first_name", user.first_name)
#         user.last_name = telegram_user_data.get("last_name", user.last_name)
#         user.avatar_url = telegram_user_data.get("photo_url", user.avatar_url)
#         user.save()

#     # Create session for the user
#     login(request, user)

#     serializer = UserSerializer(user)
#     csrf_token = get_token(request)

#     return Response({
#         "success": True,
#         "user": serializer.data,
#         "csrf_token": csrf_token,
#     }, status=status.HTTP_200_OK)
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














