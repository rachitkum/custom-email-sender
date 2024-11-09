# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('oauth/google/login/', views.google_login, name='google_login'),
    path('oauth/google/callback/', views.google_callback, name='google_callback'),
    path('send_bulk_emails/', views.send_bulk_emails, name='send_bulk_emails'),
]
