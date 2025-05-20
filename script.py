import requests
import random
import time
from uuid import uuid4
from threading import Thread

# GA4 Measurement Protocol setup
MEASUREMENT_ID = 'G-WN4L23Q7SW'
API_SECRET = '9Brw9QJdRXGpipOo7ntsgg'

# Sample data
first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry']
domains = ['example.com', 'demo.org', 'test.net']
pages = [
    {'page_location': 'https://example.com/home', 'page_title': 'Home'},
    {'page_location': 'https://example.com/about', 'page_title': 'About Us'},
    {'page_location': 'https://example.com/contact', 'page_title': 'Contact'},
    {'page_location': 'https://example.com/features', 'page_title': 'Features'},
    {'page_location': 'https://example.com/dashboard', 'page_title': 'Dashboard'}
]

# Generate fake email
def generate_email():
    return f"{random.choice(first_names).lower()}{random.randint(100,999)}@{random.choice(domains)}"

# Send single page view event
def send_event(client_id, page, email):
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"
    payload = {
        "client_id": client_id,
        "events": [
            {
                "name": "page_view",
                "params": {
                    "page_location": page['page_location'],
                    "page_title": page['page_title'],
                    "email": email  # Optional custom param
                }
            }
        ]
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Sent event for {email} | Status: {response.status_code}")
    except Exception as e:
        print(f"Error sending event: {e}")

# Simulate a single active user
def simulate_user():
    client_id = str(uuid4())
    email = generate_email()
    page = random.choice(pages)
    send_event(client_id, page, email)

# Main loop: run every second
def main():
    print("🚀 Starting simulation of 300–400 active users every second...")
    while True:
        user_count = random.randint(300, 400)
        threads = []

        for _ in range(user_count):
            thread = Thread(target=simulate_user)
            thread.start()
            threads.append(thread)

        # Optional: wait for all threads to finish (or skip to continue fast)
        for thread in threads:
            thread.join()

        print(f"✅ Sent {user_count} active users this second.\n")
        time.sleep(1)

if __name__ == "__main__":
    main()
