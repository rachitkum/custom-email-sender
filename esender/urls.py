# # urls.py
# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.home, name='home'),
#     path('oauth/google/login/', views.google_login, name='google_login'),
#     path('oauth/google/callback/', views.google_callback, name='google_callback'),
#     path('send_bulk_emails/', views.send_bulk_emails, name='send_bulk_emails'),
#     path('send_email_task/', views.send_email_task, name='send_email_task'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('api/google-login/', views.google_login, name='google_login'),
    path('api/google-callback/', views.google_callback, name='google_callback'),
    path('api/upload-csv/', views.upload_csv, name='upload_csv'),
    path('api/send-bulk-emails/', views.send_bulk_emails, name='send_bulk_emails'),
    path('api/logout/', views.logout_user, name='logout_user'),
    path('api/send-event/', views.send_analytics_event),
    
]
