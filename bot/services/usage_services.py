from datetime import date
from bot.models import UsageTracker

def get_usage_count(user):
    """
    Returns total usage count for the given SQLAlchemy user.
    """
    if not user.usage:
        return 0
    return user.usage.count


def increase_usage(session, user):
    """
    Increases usage by 1 or initializes it for new users.
    """
    if not user.usage:
        tracker = UsageTracker(user_id=user.id, count=1)
        session.add(tracker)
        session.commit()
        return 1

    user.usage.count += 1
    user.usage.date = date.today()
    session.commit()
    return user.usage.count
