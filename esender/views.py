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


def home(request):
    user_email = request.session.get('user_email')
    csv_filename = request.session.get('csv_filename')
    csv_rows = request.session.get('csv_rows', [])


    column_names = []
    if csv_rows:
        column_names = [key for key in csv_rows[0].keys() if key.lower() != 'email']

    if request.method == "POST":
   
        if request.FILES.get("csv_file"):
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
            del request.session['user_email']
            del request.session['google_access_token']
            return redirect('home')


        elif 'remove_csv' in request.POST:
            del request.session['csv_filename']
            del request.session['csv_rows']
            return redirect('home')

        elif 'send_emails' in request.POST:
        
            prompt = request.POST.get('custom_prompt')
            if prompt and csv_rows:
                try:
                    send_bulk_emails(request, prompt, csv_rows)
                    return HttpResponse("Emails sent successfully!")
                except Exception as e:
                    return HttpResponse(f"Error sending emails: {e}")

    return render(request, 'esender/home.html', {
        'user_email': user_email,
        'csv_filename': csv_filename,
        'csv_rows': csv_rows,
        'column_names': column_names
    })


def send_bulk_emails(request, prompt, csv_data):
    access_token = request.session.get('google_access_token')
    if not access_token:
        return HttpResponse("User not authenticated with Google.", status=401)

    credentials = Credentials(access_token)
    service = build('gmail', 'v1', credentials=credentials)

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

        except HttpError as error:
            print(f"An error occurred: {error}")