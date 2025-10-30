
from asgiref.sync import sync_to_async

from users.models import User

@sync_to_async
def register_telegram_user(telegram_user):
    user, created = User.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            "username": telegram_user.username or f"user_{telegram_user.id}",
            "first_name": telegram_user.first_name,
            "last_name": telegram_user.last_name,
        },
    )
    return user, created
