import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
import csv


def google_login(request):

    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&scope=email profile"
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

    if request.method == "POST":

        if request.FILES.get("csv_file"):
            csv_file = request.FILES["csv_file"]
            try:
                csv_filename = csv_file.name
                request.session['csv_filename'] = csv_filename

                csv_data = csv_file.read().decode('utf-8').splitlines()
                reader = csv.reader(csv_data)

                return render(request, 'esender/home.html', {'user_email': user_email, 'csv_filename': csv_filename})
            except Exception as e:
                return HttpResponse(f"Error processing the CSV file: {e}")


        elif 'remove_email' in request.POST:
            del request.session['user_email']
            del request.session['google_access_token']
            return render(request, 'esender/home.html', {'user_email': None, 'csv_filename': csv_filename})
        elif 'remove_csv' in request.POST:
            del request.session['csv_filename']
            return render(request, 'esender/home.html', {'user_email': user_email, 'csv_filename': None})
    return render(request, 'esender/home.html', {'user_email': user_email, 'csv_filename': csv_filename})
