import requests
import json
from datetime import datetime

# Placeholders for API keys and IDs
FEEDLY_API_KEY = "YOUR_FEEDLY_API_KEY"
FEEDLY_STREAM_ID = "YOUR_FEEDLY_STREAM_ID"
PAGERDUTY_ROUTING_KEY = "YOUR_PAGERDUTY_ROUTING_KEY"

# Maximum number of articles to fetch from Feedly (limit = 100)
FEEDLY_COUNT = 100
# Time range in milliseconds to look back for new articles (15 minutes = 900000 ms; 24 hours = 86400000 ms)
FEEDLY_NEWER_THAN = -86400000

# URLs
FEEDLY_API_URL = f"https://api.feedly.com/v3/streams/contents?streamId={FEEDLY_STREAM_ID}&count={FEEDLY_COUNT}&newerThan={FEEDLY_NEWER_THAN}"
PAGERDUTY_API_URL = "https://events.pagerduty.com/v2/enqueue"

def get_feedly_articles():
    print(f"Fetching articles from Feedly: {FEEDLY_API_URL}")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {FEEDLY_API_KEY}"
    }
    response = requests.get(FEEDLY_API_URL, headers=headers)
    print(f"Feedly API response status code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error fetching articles: {response.text}")
        return None
    return response.json()

def send_pagerduty_alert(article):
    title = article.get('title', 'No title')
    # link = article.get('alternate', [{}])[0].get('href', 'No link')
    link = f"https://feedly.com/i/entry/{article['id']}" # Use the Feedly link instead of the original article link

    # Extract sentences from LeoSummary
    leo_summary = article.get('leoSummary', {}).get('sentences', [])
    content = ' '.join([sentence.get('text', '') for sentence in leo_summary])
    
    payload = {
        "routing_key": PAGERDUTY_ROUTING_KEY,
        "event_action": "trigger",
        "payload": {
            "summary": f"New Feedly Alert: {title}",
            "source": "Feedly via Python Script",
            "severity": "info",
            "custom_details": {
                "link": link,
                "content": content
            }
        }
    }
    
    print(f"Sending PagerDuty alert for article: {title}")
    print(f"PagerDuty payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(PAGERDUTY_API_URL, json=payload)
    print(f"PagerDuty API response status code: {response.status_code}")
    
    # PagerDuty Events API v2 returns 202 Accepted on success
    # This indicates the event was successfully enqueued for processing
    if response.status_code == 202:
        print("PagerDuty alert sent successfully")
        return True
    else:
        print(f"Failed to send PagerDuty alert: {response.text}")
        return False

def main():
    print(f"Script started at {datetime.now()}")
    articles = get_feedly_articles()
    
    if articles is None:
        print("No articles fetched. Exiting.")
        return
    
    print(f"Number of articles fetched: {len(articles.get('items', []))}")
    
    for article in articles.get('items', []):
        if send_pagerduty_alert(article):
            print(f"Alert sent for article: {article.get('title', 'No title')}")
        else:
            print(f"Failed to send alert for article: {article.get('title', 'No title')}")
        print("-" * 50)  # Separator between articles
    
    print(f"Script completed at {datetime.now()}")

if __name__ == "__main__":
    main()