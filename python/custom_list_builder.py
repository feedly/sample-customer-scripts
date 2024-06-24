import requests
import pandas as pd

API_KEY = 'YOUR API KEY' # Add your API key here
CSV_FILE_PATH = 'YOUR CSV FILE PATH' # Add the absolute or relative CSV file path here (the CSV should only contain a single column with the entities)
BASE_URL = 'https://api.feedly.com/v3'

def get_entity_id(query, api_key):
    url = f"{BASE_URL}/search/entities?query={query.replace(' ', '%20')}"
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to fetch data for {query}')
        return None

def process_queries(query_list, api_key):
    entities = []
    for query in query_list:
        result = get_entity_id(query, api_key)
        if result and result.get('entities'):
            entity_id = result['entities'][0]['id']
            entities.append({'id': entity_id})
        else:
            entities.append({'text': query})
    return entities

def build_payload(query_list, api_key, label='API Custom List'): # Change the name of your Custom List here
    processed_entities = process_queries(query_list, api_key)
    payload = {
        'label': label,
        'entities': processed_entities,
        'type': 'customTopic'
    }
    return payload

def post_payload(api_key, payload):
    url = f'{BASE_URL}/enterprise/entityLists'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200 or response.status_code == 204:
        print('Payload successfully posted.')
    else:
        print(f'Failed to post payload: {response.status_code} - {response.text}')
    return response

def main():
    df = pd.read_csv(CSV_FILE_PATH)
    query_list = df.iloc[:, 0].tolist()
    payload = build_payload(query_list, API_KEY)
    response = post_payload(API_KEY, payload)
    print(response.text)

if __name__ == '__main__':
    main()

