import requests
from datetime import datetime, timedelta
from django.conf import settings

SENDGRID_API_KEY = settings.SENDGRID_API_KEY  # Make sure to set the key in your settings

def get_sendgrid_email_stats():
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    # Get total emails sent in the last 24 hours
    params = {
        'start_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'end_date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    # Get statistics from SendGrid
    response = requests.get("https://api.sendgrid.com/v3/stats", headers=headers, params=params)
    
    if response.status_code == 200:
        stats = response.json()
        
        total_sent = sum([stat['metrics']['sent'] for stat in stats if 'sent' in stat['metrics']])
        total_delivered = sum([stat['metrics']['delivered'] for stat in stats if 'delivered' in stat['metrics']])
        total_bounced = sum([stat['metrics']['bounced'] for stat in stats if 'bounced' in stat['metrics']])
        total_complaints = sum([stat['metrics']['complaints'] for stat in stats if 'complaints' in stat['metrics']])

        # Assuming failure means bounces or complaints
        failed = total_bounced + total_complaints
        pending = total_sent - total_delivered - failed
        
        response_rate = (total_delivered / total_sent) * 100 if total_sent > 0 else 0

        return {
            "total_sent": total_sent,
            "pending": pending,
            "scheduled": 0,  # You will need to track this separately
            "failed": failed,
            "response_rate": response_rate
        }
    else:
        print(f"Failed to fetch SendGrid stats: {response.status_code}")
        return {}
