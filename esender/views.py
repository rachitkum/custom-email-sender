from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import requests
import csv
import base64
import re
import pytz
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from datetime import datetime
from .models import EmailStatus

# Google login API
@api_view(['GET'])
def google_login(request):
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8081/google-callback/"
        "&scope=email profile https://www.googleapis.com/auth/gmail.send"
        "&response_type=code"
        "&access_type=offline"
    )
    return JsonResponse({"auth_url": auth_url})


# Google OAuth Callback API
@api_view(['GET'])
def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return Response({"error": "No authorization code received"}, status=400)

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    access_token = token_json.get('access_token')
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
    user_info_json = user_info_response.json()
    
    user_email = user_info_json.get('email')

    request.session['user_email'] = user_email
    request.session['google_access_token'] = access_token

    return Response({"message": "User authenticated", "email": user_email})


# API to Upload CSV
@api_view(['POST'])
def upload_csv(request):
    if 'csv_file' not in request.FILES:
        return Response({"error": "No CSV file uploaded"}, status=400)

    csv_file = request.FILES['csv_file']
    try:
        csv_data = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(csv_data)
        rows = [row for row in reader]

        request.session['csv_rows'] = rows
        return Response({"message": "CSV uploaded successfully", "rows": rows})
    except Exception as e:
        return Response({"error": f"Error processing CSV: {str(e)}"}, status=500)


# Initialize or get the email status
def get_or_create_email_status():
    email_status, created = EmailStatus.objects.get_or_create(id=1)
    return email_status


# API to Send Bulk Emails
@api_view(['POST'])
def send_bulk_emails(request):

    access_token = request.session.get('google_access_token')
    if not access_token:
        return Response({"error": "User not authenticated with Google"}, status=401)

    credentials = Credentials(access_token)
    service = build('gmail', 'v1', credentials=credentials)
    data = request.data 
    prompt = data.get('prompt')
    csv_rows = data.get('csv_rows', [])

    if not prompt or not csv_rows:
        return Response({"error": "Prompt and CSV data are required"}, status=400)

    email_status = get_or_create_email_status()

    for row in csv_rows:
        email = row.get('email')
        if not email:
            continue

        personalized_content = prompt
        matches = re.findall(r'\{([^}]+)\}', prompt)

        for match in matches:
            match_clean = match.strip().lower()
            for key, value in row.items():
                if key.strip().lower() == match_clean:
                    placeholder = f"{{{match}}}"
                    personalized_content = personalized_content.replace(placeholder, value)

        try:
            message = MIMEText(personalized_content)
            message['To'] = email
            message['Subject'] = "Custom Subject"
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            email_status.update_status('sent')
        except HttpError as error:
            email_status.update_status('failed')

    email_status.calculate_response_rate()
    return Response({"message": "Emails sent successfully"})


# API to Remove User Session
@api_view(['POST'])
def logout_user(request):
    request.session.flush()
    return Response({"message": "Logged out successfully"})

# def send_bulk_emails(request, prompt, csv_data):
#     access_token = request.session.get('google_access_token')
#     if not access_token:
#         return HttpResponse("User not authenticated with Google.", status=401)

#     credentials = Credentials(access_token)
#     service = build('gmail', 'v1', credentials=credentials)
    
#     email_status = get_or_create_email_status()

#     for row in csv_data:
#         email = row.get('Email')
#         personalized_content = prompt
#         matches = re.findall(r'\{([^}]+)\}', prompt)

#         for match in matches:
#             match_clean = match.strip().lower()
#             for key, value in row.items():
#                 if key.strip().lower() == match_clean:
#                     placeholder = f"{{{match}}}"
#                     personalized_content = personalized_content.replace(placeholder, value)

#         try:
#             message_content = f"To: {email}\nSubject: Custom Subject\n\n{personalized_content}"
#             raw_message = base64.urlsafe_b64encode(message_content.encode('utf-8')).decode('utf-8')
#             message = {'raw': raw_message}
#             message_sent = service.users().messages().send(userId='me', body=message).execute()
#             email_status.update_status('sent')
#         except HttpError as error:
#             email_status.update_status('failed')
    
#     email_status.calculate_response_rate()


# def send_bulk_emails_with_schedule(request, prompt, csv_data, schedule_time):

#     ist_timezone = pytz.timezone('Asia/Kolkata')
    
#     # Convert the send time to datetime object
#     try:
        
#         schedule_time = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')  
        
       
#         schedule_time = ist_timezone.localize(schedule_time)
#     except ValueError:
#         return HttpResponse("Invalid date format. Please use YYYY-MM-DDTHH:MM.", status=400)

    
#     if schedule_time <= timezone.now():
        
#         send_bulk_emails(request, prompt, csv_data)
#         return HttpResponse("Scheduled time is in the past. Emails sent immediately.")
    
    
#     access_token = request.session.get('google_access_token')
#     if not access_token:
#         return HttpResponse("User not authenticated with Google.", status=401)
#     email_status = get_or_create_email_status() 
#     email_status.total_scheduled += len(csv_data) 
#     email_status.save()
  
#     send_email_task.apply_async(
#         (access_token, prompt, csv_data), 
#         eta=schedule_time
#     )

#     return HttpResponse(f"Emails are scheduled for {schedule_time}.")

