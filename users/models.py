#tenabot/users/models.py
from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, telegram_id, username=None, email=None, password=None, **extra_fields):
        if not telegram_id:
            raise ValueError("Users must have a Telegram ID")
        email = self.normalize_email(email)
        user = self.model(telegram_id=telegram_id, username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(telegram_id, username, email, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    telegram_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=150, null=True, blank=True)
    avatar_url = models.URLField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username or self.telegram_id}"
    
    


