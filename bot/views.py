from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'bot/bot.html')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from users.models import User



