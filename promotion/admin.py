from django.contrib import admin
from .models import Sponsor, PromoChannel, AdCampaign, Package

admin.site.register(Sponsor)
admin.site.register(PromoChannel)
admin.site.register(AdCampaign)
admin.site.register(Package)
