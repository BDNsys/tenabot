import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tenabot.settings")

import django
django.setup()

from promotion.models import AdCampaign


def get_active_promotion():
    return AdCampaign.objects.filter(is_active=True).order_by('-id').first()
