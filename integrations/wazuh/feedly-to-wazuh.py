import requests
import json
from stix2 import parse
from datetime import datetime

# Feedly API configuration
FEEDLY_API_BASE_URL = "https://feedly.com/v3/enterprise/ioc"
FEEDLY_API_KEY = "YOUR_FEEDLY_API_KEY"
FEEDLY_STREAM_ID = "YOUR_FEEDLY_STREAM_ID"

# Wazuh API configuration
WAZUH_API_URL = "https://your-wazuh-manager:55000"
WAZUH_API_USER = "your-wazuh-api-user"
WAZUH_API_PASSWORD = "your-wazuh-api-password"

def fetch_feedly_data():
    headers = {
        'Authorization': FEEDLY_API_KEY
    }
    url = f"{FEEDLY_API_BASE_URL}?streamid={FEEDLY_STREAM_ID}"
    response = requests.get(url, headers=headers)
    return response.json()

def parse_stix_data(stix_data):
    bundle = parse(stix_data)
    indicators = []
    for obj in bundle.objects:
        if obj.type == 'indicator':
            indicators.append({
                'type': obj.type,
                'name': obj.name,
                'pattern': obj.pattern,
                'valid_from': obj.valid_from
            })
    return indicators

def format_for_wazuh(indicators):
    wazuh_data = []
    for indicator in indicators:
        wazuh_data.append({
            "integration": "feedly",
            "feedly": {
                "name": indicator['name'],
                "type": indicator['type'],
                "pattern": indicator['pattern'],
                "valid_from": indicator['valid_from']
            }
        })
    return wazuh_data

def send_to_wazuh(data):
    headers = {
        'Content-Type': 'application/json'
    }
    auth = (WAZUH_API_USER, WAZUH_API_PASSWORD)
    
    for item in data:
        response = requests.post(f"{WAZUH_API_URL}/events", 
                                 headers=headers, 
                                 auth=auth, 
                                 data=json.dumps(item))
        if response.status_code == 200:
            print(f"Successfully sent indicator: {item['feedly']['name']}")
        else:
            print(f"Failed to send indicator: {item['feedly']['name']}. Status code: {response.status_code}")

def main():
    # Fetch data from Feedly
    feedly_data = fetch_feedly_data()
    
    # Parse STIX data
    indicators = parse_stix_data(feedly_data)
    
    # Format for Wazuh
    wazuh_data = format_for_wazuh(indicators)
    
    # Send to Wazuh
    send_to_wazuh(wazuh_data)

if __name__ == "__main__":
    main()
