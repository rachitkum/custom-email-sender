


# Endpoint to send events
import requests
import random
import time
from uuid import uuid4

# Replace with your real GA4 Measurement ID and API Secret
MEASUREMENT_ID = 'G-WN4L23Q7SW'
API_SECRET = '9Brw9QJdRXGpipOo7ntsgg'  # From Admin > Data Streams > Measurement Protocol

# Email generators
first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
domains = ['example.com', 'demo.org', 'test.net']

def generate_email():
    return f"{random.choice(first_names).lower()}{random.randint(100,999)}@{random.choice(domains)}"

# Send event to GA4 (WITHOUT debug_mode)
def send_event(client_id, email, event_name):
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"
    payload = {
        "client_id": client_id,
        "events": [
            {
                "name": event_name,
                "params": {
                    "email": email,
                    # Custom parameters go here
                }
            }
        ]
    }

    response = requests.post(url, json=payload)
    print(f"✅ Sent {event_name} for {email} | Status: {response.status_code}")

# Main logic to create fake users
def main():
    for _ in range(10):
        email = generate_email()
        client_id = str(uuid4())  # Random unique user ID

        # Randomly pick new or returning
        event_name = random.choice(['new_user', 'returning_user'])
        send_event(client_id, email, event_name)
        
        time.sleep(1)  # avoid rate-limiting

if __name__ == "__main__":
    main()
