import requests
import json
import sys
import logging
from datetime import datetime, timedelta, timezone

# Constants for the Feedly API
FEEDLY_API_URL = "https://feedly.com/v3/enterprise/ioc"
FEEDLY_STREAM_ID = "YOUR_FEEDLY_STREAM_ID" 
FEEDLY_BEARER_TOKEN = "YOUR_FEEDLY_BEARER_TOKEN"
FEEDLY_HEADERS = {
    'Authorization': f'Bearer {FEEDLY_BEARER_TOKEN}'
}

# Constants for the Splunk HEC
SPLUNK_HEC_URL = "YOUR_SPLUNK_HEC_ENDPOINT"
SPLUNK_HEC_TOKEN = "YOUR_SPLUNK_HEC_TOKEN"
SPLUNK_HEADERS = {
    "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
    "Content-Type": "application/json"
}

def setup_logging(debug_mode=False):
    level = logging.DEBUG if debug_mode else logging.INFO
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    return logger

def convert_interval_to_milliseconds(interval, unit):
    logger = logging.getLogger(__name__)
    unit = unit.lower()
    now = datetime.now(timezone.utc)
    current_timestamp = int(now.timestamp() * 1000)
    
    # Debug prints for current time
    logger.debug(f"Current time (UTC): {now}")
    logger.debug(f"Current timestamp (ms): {current_timestamp}")
    
    # Calculate milliseconds to subtract
    if unit == 'days':
        ms_to_subtract = int(interval) * 24 * 60 * 60 * 1000
    elif unit == 'hours':
        ms_to_subtract = int(interval) * 60 * 60 * 1000
    elif unit == 'weeks':
        ms_to_subtract = int(interval) * 7 * 24 * 60 * 60 * 1000
    else:
        raise ValueError("Invalid time unit. Please use 'days', 'hours', or 'weeks'.")
    
    logger.debug(f"Milliseconds to subtract: {ms_to_subtract}")
    
    # Calculate final timestamp
    final_timestamp = current_timestamp - ms_to_subtract
    final_time = datetime.fromtimestamp(final_timestamp / 1000, tz=timezone.utc)
    
    logger.debug(f"Final timestamp (ms): {final_timestamp}")
    logger.debug(f"Final time (UTC): {final_time}")
    logger.debug(f"Time difference: {now - final_time}")
    
    return final_timestamp

def fetch_feedly_data(newer_than):
    logger = logging.getLogger(__name__)
    logger.debug(f"fetch_feedly_data received newer_than value: {newer_than}")
    
    params = {
        "newerThan": newer_than,
        "streamId": FEEDLY_STREAM_ID
    }
    
    logger.debug(f"API request params: {json.dumps(params)}")
    
    response = requests.get(FEEDLY_API_URL, headers=FEEDLY_HEADERS, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if not data.get("objects"):
            logger.info(f"No articles found in the specified time period (newer than {newer_than})")
        return data
    else:
        logger.error(f"Error fetching data from Feedly: {response.status_code}")
        logger.error(f"Response text: {response.text}")
        return None

def send_to_splunk(data):
    logger = logging.getLogger(__name__)
    headers = {
        "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
        "Content-Type": "application/json"
    }

    for event in data["objects"]:
        event_data = json.dumps({"event": event})
        
        # Make the POST request to the Splunk HEC for each event
        response = requests.post(SPLUNK_HEC_URL, headers=headers, data=event_data, verify=False)
        
        if response.status_code == 200:
            logger.info("Event sent to Splunk successfully.")
        else:
            logger.error(f"Error sending event to Splunk: {response.status_code}")
            logger.error(f"Response text: {response.text}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <interval> <unit> [--debug]")
        print("<interval> is a number indicating how far back to look for indicators.")
        print("<unit> is either 'days', 'hours', or 'weeks'.")
        print("--debug: Enable debug mode for detailed output")
        sys.exit(1)
    
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        sys.argv.remove("--debug")
    
    logger = setup_logging(debug_mode)
    
    interval = sys.argv[1]
    unit = sys.argv[2]
    
    logger.debug(f"Command line arguments: interval={interval}, unit={unit}")
    
    try:
        newer_than_milliseconds = convert_interval_to_milliseconds(interval, unit)
        logger.debug(f"Converted to milliseconds: {newer_than_milliseconds}")
    except ValueError as e:
        logger.error(f"Invalid time unit: {e}")
        sys.exit(1)
    
    feedly_data = fetch_feedly_data(newer_than_milliseconds)
    
    if feedly_data:
        send_to_splunk(feedly_data)

if __name__ == "__main__":
    main()

