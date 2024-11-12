from celery import shared_task
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.http import HttpResponse 
import base64
import re
from googleapiclient.errors import HttpError
@shared_task
def send_email_task(access_token, prompt, csv_data):
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
            service.users().messages().send(userId='me', body=message).execute()
        except HttpError as error:
            print(f"An error occurred: {error}")



