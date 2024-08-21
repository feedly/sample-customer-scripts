import json
import re
import requests
import time

# Three hours ago in milliseconds if your scheduled job run every three hours
three_hours_ago = int(time.time() * 1000) - 10800000

# Add endpoint & stream ID / Analyst 2 board
url = "https://api.feedly.com/v3/streams/contents?streamID=[Add stream ID for folders to sharing]"

headers = {
    "accept": "application/json",
    "Authorization": "[INSERT API TOKEN from Feedly]"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    new_articles_found = False

    # Extract relevant articles and URL
    for item in data['items']:
        saved_timestamp = item.get('actionTimestamp')
        if saved_timestamp and saved_timestamp > three_hours_ago:
            title = item.get('title')
            #summary = item.get('summary',{}).get('content', '')
            # If the tilte is none
            if not title:
                summary = item.get('summary', {}).get('content', '')
                # Remove HTML paragraph tag
                title = re.sub(r'<.*?>', summary)
            # Get link to feedly article
            link = 'https://feedly.com/i/entry/'+item.get('id')
            # Get image

            # Matrix room
            access_token = 'Matrix Access Token'
            room_id = '[Matrix Room id]:matrix.org'
            matrix_url = f"https://matrix.org/_matrix/client/r0/rooms/{room_id}/send/m.room.message?access_token={access_token}"

            # Send content
            message_content = {
                "msgtype": "m.text",
                "body": f"**{title}**\n\nRead more at: {link}"
            }

            response = requests.post(matrix_url, headers={"Content-Type": "application/json"}, data=json.dumps(message_content))
            if response.status_code == 200:
                print(f"Text message sent to room {room_id}")
            else:
                print(f"Failed to send message with status {response.status_code}. Response: {response.text}")
    if not new_articles_found:
        print('No new articles in the last three hours')

else:
    print(f"Failed to retrieve data with status code {response.status_code}")