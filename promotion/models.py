from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Sponsor(models.Model):
    name = models.CharField(max_length=255)
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    contact_telegram = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


class PromoChannel(models.Model):
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name="channels")
    channel_name = models.CharField(max_length=255)
    channel_link = models.URLField()   # https://t.me/xxxx

    def __str__(self):
        return f"{self.channel_name} ({self.sponsor.name})"



    
    
class Package(models.Model):
    title= models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    number_of_people=models.IntegerField()
    fee= models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.title} - {self.number_of_people}"
    
class AdCampaign(models.Model):
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name="campaigns")
    channel = models.ForeignKey(PromoChannel, on_delete=models.CASCADE, related_name="ads")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="package")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.sponsor.name}"
    
    
