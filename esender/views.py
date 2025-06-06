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
from django.http import HttpResponseRedirect
from .models import EmailStatus
GA_MEASUREMENT_ID = 'G-WN4L23Q7SW'
GA_API_SECRET = '9Brw9QJdRXGpipOo7ntsgg'

def get_or_create_email_status(user_email):
    return EmailStatus.objects.get_or_create(user_email=user_email)[0]

def get_user_email_from_token(access_token):
    try:
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        user_info_json = user_info_response.json()
        return user_info_json.get("email")
    except:
        return None


@api_view(['POST'])
def send_event_to_ga(request):
    payload = request.data

    # Validate required fields
    client_id = payload.get("client_id")
    events = payload.get("events")

    if not client_id or not events:
        return Response({"error": "Missing 'client_id' or 'events'"}, status=400)

    # Build Google Analytics URL
    ga_url = (
        f"https://www.google-analytics.com/mp/collect"
        f"?measurement_id={GA_MEASUREMENT_ID}"
        f"&api_secret={GA_API_SECRET}"
    )

    try:
        response = requests.post(ga_url, json=payload)
        if response.status_code != 204:
            return Response({
                "status": "sent_with_warning",
                "response_code": response.status_code,
                "details": response.text,
            }, status=200)

        return Response({"status": "✅ Event sent", "response_code": 204})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# Google login API
@api_view(['GET'])
def google_login(request):
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"       
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
    if not access_token:
        return Response({"error": "Failed to retrieve access token"}, status=400)

    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
    user_info_json = user_info_response.json()

    user_email = user_info_json.get('email')
    if not user_email:
        return Response({"error": "Failed to retrieve user email"}, status=400)

    # Save user email and token in session
    request.session['user_email'] = user_email
    request.session['google_access_token'] = access_token

    # Create or update EmailStatus for this user_email
    email_status, created = EmailStatus.objects.get_or_create(user_email=user_email)
    if created:
        # Initialized with default zeros from model
        pass
    else:
        # Optionally reset or keep stats (up to you)
        pass

    # Redirect back to frontend with token and email in query params
    # FRONTEND_REDIRECT_URI = "http://localhost:8081/"  # or your production URL
    FRONTEND_REDIRECT_URI = "https://bulkmailsender.netlify.app"

    redirect_url = f"{FRONTEND_REDIRECT_URI}?token={access_token}&email={user_email}"
    return HttpResponseRedirect(redirect_url)

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
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"error": "User not authenticated with Google"}, status=401)

    access_token = auth_header.split(' ')[1]
    
    # ✅ Get user email from Google API using access token
    user_email = get_user_email_from_token(access_token)
    if not user_email:
        return Response({"error": "Unable to retrieve user email"}, status=401)

    # Create credentials and Gmail service
    credentials = Credentials(access_token)
    service = build('gmail', 'v1', credentials=credentials)

    data = request.data
    prompt = data.get('prompt')
    csv_rows = data.get('csv_rows', [])

    if not prompt or not csv_rows:
        return Response({"error": "Prompt and CSV data are required"}, status=400)

    # ✅ Get or create analytics entry for this user
    email_status, _ = EmailStatus.objects.get_or_create(user_email=user_email)

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
        except HttpError:
            email_status.update_status('failed')

    email_status.calculate_response_rate()

    total_attempts = email_status.total_sent + email_status.total_failed
    success_rate = round((email_status.total_sent / total_attempts) * 100, 2) if total_attempts > 0 else 0.0
    failure_rate = round((email_status.total_failed / total_attempts) * 100, 2) if total_attempts > 0 else 0.0
    analytics = {
        "total_sent": email_status.total_sent,
        "total_failed": email_status.total_failed,
        "total_attempts": total_attempts,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "response_rate": email_status.response_rate,
    }

    return Response({
        "message": "Emails sent successfully",
        "analytics": analytics
    })

# API to Remove User Session
@api_view(['POST'])
def logout_user(request):
    request.session.flush()
    return Response({"message": "Logged out successfully"})

@api_view(['GET'])
def get_user_analytics(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"error": "User not authenticated with Google"}, status=401)

    access_token = auth_header.split(' ')[1]
    print(access_token)
    user_email = get_user_email_from_token(access_token)
    if not user_email:
        return Response({"error": "Unable to retrieve user email"}, status=401)

    try:
        email_status = EmailStatus.objects.get(user_email=user_email)
        total_attempts = email_status.total_sent + email_status.total_failed
        success_rate = round((email_status.total_sent / total_attempts) * 100, 2) if total_attempts > 0 else 0.0
        failure_rate = round((email_status.total_failed / total_attempts) * 100, 2) if total_attempts > 0 else 0.0

        return Response({
            "user_email": user_email,
            "total_scheduled": email_status.total_scheduled,
            "total_sent": email_status.total_sent,
            "total_failed": email_status.total_failed,
            "response_rate": email_status.response_rate,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
        })
    except EmailStatus.DoesNotExist:
        return Response({"error": "No analytics found for this user"}, status=404)




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

