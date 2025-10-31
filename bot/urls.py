from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('upload-resume/', views.ResumeUploadView.as_view(), name='upload-resume')
    
 
]
