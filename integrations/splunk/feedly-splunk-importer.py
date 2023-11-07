import requests
import json
import sys
from datetime import datetime, timedelta

# Constants for the Feedly API
FEEDLY_API_URL = "https://feedly.com/v3/enterprise/ioc"
FEEDLY_STREAM_ID = "YOUR_FEEDLY_STREAM_ID"  # Replace with your Feedly stream ID
FEEDLY_BEARER_TOKEN = "YOUR_FEEDLY_BEARER_TOKEN"  # Replace with your Feedly API token
FEEDLY_HEADERS = {
    'Authorization': f'Bearer {FEEDLY_BEARER_TOKEN}'
}

# Constants for the Splunk HEC
SPLUNK_HEC_URL = "YOUR_SPLUNK_HEC_ENDPOINT"  # Replace with your Splunk HEC endpoint
SPLUNK_HEC_TOKEN = "YOUR_SPLUNK_HEC_TOKEN"  # Replace with your Splunk HEC token
SPLUNK_HEADERS = {
    "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
    "Content-Type": "application/json"
}

def convert_interval_to_milliseconds(interval, unit):
    """
    Converts an interval and its unit (days, hours, weeks) into milliseconds.
    """
    unit = unit.lower()
    now = datetime.utcnow()
    
    if unit == 'days':
        return int((now - timedelta(days=int(interval))).timestamp() * 1000)
    elif unit == 'hours':
        return int((now - timedelta(hours=int(interval))).timestamp() * 1000)
    elif unit == 'weeks':
        return int((now - timedelta(weeks=int(interval))).timestamp() * 1000)
    else:
        raise ValueError("Invalid time unit. Please use 'days', 'hours', or 'weeks'.")

def fetch_feedly_data(newer_than):
    """
    Fetches the STIX 2.1 JSON export for indicators from Feedly based on the 'newerThan' parameter.
    """
    # Set up the parameters for the API request
    params = {
        "newerThan": newer_than,
        "streamId": FEEDLY_STREAM_ID
    }
    
    # Make the request to the Feedly API
    response = requests.get(FEEDLY_API_URL, headers=FEEDLY_HEADERS, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()  # Return the JSON response
    else:
        # Log an error if something went wrong
        print(f"Error fetching data from Feedly: {response.status_code}")
        print(response.text)
        return None

def send_to_splunk(data):
    """
    Sends the given data to the Splunk HEC endpoint.
    """
    # Make the POST request to the Splunk HEC
    response = requests.post(SPLUNK_HEC_URL, headers=SPLUNK_HEADERS, data=json.dumps({"event": data}), verify=False)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("Data sent to Splunk successfully.")
    else:
        # Log an error if something went wrong
        print(f"Error sending data to Splunk: {response.status_code}")
        print(response.text)

def main():
    """
    Main function to fetch data from Feedly and send to Splunk.
    """
    # Parse the interval and unit from the command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <interval> <unit>")
        print("<interval> is a number indicating how far back to look for indicators.")
        print("<unit> is either 'days', 'hours', or 'weeks'.")
        sys.exit(1)
    
    interval = sys.argv[1]
    unit = sys.argv[2]
    
    # Convert the interval to milliseconds
    try:
        newer_than_milliseconds = convert_interval_to_milliseconds(interval, unit)
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    # Fetch the data from Feedly
    feedly_data = fetch_feedly_data(newer_than_milliseconds)
    
    # If data was fetched successfully, send it to Splunk
    if feedly_data:
        send_to_splunk(feedly_data)

# Call the main function
if __name__ == "__main__":
    main()
