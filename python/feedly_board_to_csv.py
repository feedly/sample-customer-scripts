## You will need to install requests and pandas via pip for this script to work.
## Use the following command to install the dependencies: `python -m ensurepip --default-pip && python -m pip install pandas`

import requests
import pandas as pd

count = 3
token = 'YOUR API KEY'
stream_id = 'YOUR STREAM ID'
url = f'https://feedly.com/v3/streams/contents?streamId={stream_id}&Count={count}'

payload={}
headers = {
  'Authorization': f'Bearer {token}'
}

response = requests.request('GET', url, headers=headers, data=payload)
response_dict = response.json()
article_list = response_dict['items']
df = pd.DataFrame()
for article in article_list:
    df = df.append(pd.json_normalize(article))

df.to_csv('article_data.csv')
