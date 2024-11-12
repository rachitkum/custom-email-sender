



import requests
import csv
import base64
import re
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from django.utils import timezone
from .tasks import send_email_task
from .models import EmailStatus
import pytz
from .models import EmailStatus

# Google login
def google_login(request):
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&scope=email profile https://www.googleapis.com/auth/gmail.send"
        "&response_type=code"
        "&access_type=offline"
    )
    return redirect(auth_url)


def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return HttpResponse("No authorization code received.", status=400)

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

    return redirect('home')


from django.core.cache import cache

# Initialize or get the email status
def get_or_create_email_status():
    email_status, created = EmailStatus.objects.get_or_create(id=1)
    return email_status


def update_email_status(request, status_type):
    email_status = get_or_create_email_status()
    email_status.update_status(status_type)
    email_status.calculate_response_rate()
    return email_status


def home(request):
    email_status = get_or_create_email_status()
    # Assuming you have access_token, prompt, and csv_data already
    access_token = request.session.get('google_access_token')
    prompt = request.POST.get('custom_prompt')
    csv_data = request.session.get('csv_rows', [])

    # Store these in the cache (or use the database if needed)
    cache.set('access_token', access_token, timeout=3600)  # Store for 1 hour
    cache.set('prompt', prompt, timeout=3600)
    cache.set('csv_data', csv_data, timeout=3600)
    user_email = request.session.get('user_email')
    csv_filename = request.session.get('csv_filename')
    csv_rows = request.session.get('csv_rows', [])

    column_names = []
    if csv_rows:
        column_names = [key for key in csv_rows[0].keys() if key.lower() != 'email']

    if request.method == "POST":
        if request.FILES.get("csv_file"):
            # Handle CSV file upload
            csv_file = request.FILES["csv_file"]
            try:
                csv_filename = csv_file.name
                request.session['csv_filename'] = csv_filename

                csv_data = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(csv_data)
                rows = [row for row in reader]

                request.session['csv_rows'] = rows
                return HttpResponse("CSV file uploaded successfully!")
            except Exception as e:
                return HttpResponse(f"Error processing the CSV file: {e}")

        elif 'remove_email' in request.POST:
            # Handle email removal
            del request.session['user_email']
            del request.session['google_access_token']
            return redirect('home')

        elif 'remove_csv' in request.POST:
            # Handle CSV removal
            del request.session['csv_filename']
            del request.session['csv_rows']
            return redirect('home')

        elif 'send_emails' in request.POST:
            # Handle sending emails (either immediately or scheduled)
            prompt = request.POST.get('custom_prompt')
            schedule_checkbox = request.POST.get('schedule_checkbox')
            schedule_time = request.POST.get('schedule_time')

            if prompt and csv_rows:
                # If scheduling is checked
                if schedule_checkbox == 'true' and schedule_time:
                    # Call function to schedule emails
                    return send_bulk_emails_with_schedule(request, prompt, csv_rows, schedule_time)
                else:
                    # Send emails immediately if no schedule time
                    try:
                        send_bulk_emails(request, prompt, csv_rows)
                        return HttpResponse("Emails sent successfully!")
                    except Exception as e:
                        return HttpResponse(f"Error sending emails: {e}")
            else:
                return HttpResponse("Please provide a custom prompt and upload a CSV file.")

    return render(request, 'esender/home.html', {
        'user_email': user_email,
        'csv_filename': csv_filename,
        'csv_rows': csv_rows,
        'column_names': column_names,
        'email_status': email_status,
    })

def send_bulk_emails(request, prompt, csv_data):
    access_token = request.session.get('google_access_token')
    if not access_token:
        return HttpResponse("User not authenticated with Google.", status=401)

    credentials = Credentials(access_token)
    service = build('gmail', 'v1', credentials=credentials)
    
    email_status = get_or_create_email_status()

    for row in csv_data:
        email = row.get('Email')
        personalized_content = prompt
        matches = re.findall(r'\{([^}]+)\}', prompt)

        for match in matches:
            match_clean = match.strip().lower()
            for key, value in row.items():
                if key.strip().lower() == match_clean:
                    placeholder = f"{{{match}}}"
                    personalized_content = personalized_content.replace(placeholder, value)

        try:
            message_content = f"To: {email}\nSubject: Custom Subject\n\n{personalized_content}"
            raw_message = base64.urlsafe_b64encode(message_content.encode('utf-8')).decode('utf-8')
            message = {'raw': raw_message}
            message_sent = service.users().messages().send(userId='me', body=message).execute()
            email_status.update_status('sent')
        except HttpError as error:
            email_status.update_status('failed')
    
    email_status.calculate_response_rate()


def send_bulk_emails_with_schedule(request, prompt, csv_data, schedule_time):

    ist_timezone = pytz.timezone('Asia/Kolkata')
    
    # Convert the send time to datetime object
    try:
        
        schedule_time = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')  
        
       
        schedule_time = ist_timezone.localize(schedule_time)
    except ValueError:
        return HttpResponse("Invalid date format. Please use YYYY-MM-DDTHH:MM.", status=400)

    
    if schedule_time <= timezone.now():
        
        send_bulk_emails(request, prompt, csv_data)
        return HttpResponse("Scheduled time is in the past. Emails sent immediately.")
    
    
    access_token = request.session.get('google_access_token')
    if not access_token:
        return HttpResponse("User not authenticated with Google.", status=401)
    email_status = get_or_create_email_status() 
    email_status.total_scheduled += len(csv_data) 
    email_status.save()
  
    send_email_task.apply_async(
        (access_token, prompt, csv_data), 
        eta=schedule_time
    )

    return HttpResponse(f"Emails are scheduled for {schedule_time}.")

