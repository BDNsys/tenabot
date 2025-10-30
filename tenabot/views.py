
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from users.models import User


@csrf_exempt
def register_telegram_user_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        telegram_id = str(data.get("telegram_id"))
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": data.get("username"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "avatar_url": data.get("avatar_url"),
            },
        )
        return JsonResponse({"status": "ok", "created": created})
    return JsonResponse({"error": "Invalid method"}, status=405)


