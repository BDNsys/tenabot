

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from users.models import User
import json



@csrf_exempt
def register_telegram_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        telegram_id = data.get("telegram_id")

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": data.get("username") or f"user_{telegram_id}",
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
            },
        )

        return JsonResponse({
            "success": True,
            "created": created,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        })
    return JsonResponse({"error": "Invalid request"}, status=400)





