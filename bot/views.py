from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'bot/bot.html')

def test(request):
    return render(request, 'bot/test.html')


