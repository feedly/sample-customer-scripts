"""
Description: This script fetches article data from the Feedly API, processes it, and saves it as a CSV file.

Input: The script uses the following command-line arguments:
  --token: Your personal Feedly API key.
  --stream_id: The unique identifier for the Feedly stream.
  --article_count: The number of articles to fetch from the Feedly API.

Output: The script outputs a CSV file called 'article_data.csv' containing the processed article data.

Setting up a virtual environment and installing dependencies:

1. Install the virtualenv package if you don't have it:
   pip install virtualenv

2. Create a virtual environment in your project folder:
   python -m virtualenv venv

3. Activate the virtual environment:
   - On Windows:
     venv\Scripts\activate
   - On macOS/Linux:
     source venv/bin/activate

4. Install the required dependencies in the virtual environment:
   pip install requests pandas

Example usage:

1. To save the output as a CSV file (default):
python ioc_fetcher.py --token YOUR_API_KEY --stream_id YOUR_STREAM_ID --article_count 3
"""

import argparse
import sys
import pandas as pd
import requests

def flatten_json(d, prefix='', separator='_', max_depth=None, depth=0):
    """
    Flatten nested dictionaries and lists in JSON objects up to a specified depth.

    :param d: The input JSON object (dictionary or list) to be flattened.
    :param prefix: The prefix for nested keys (used for recursion).
    :param separator: The separator used between nested keys.
    :param max_depth: The maximum depth to flatten (None for no limit).
    :param depth: The current depth (used for recursion).
    :return: A flattened dictionary.
    """
    flattened = {}

    if max_depth is not None and depth >= max_depth:
        return {prefix: d}

    if isinstance(d, dict):
        for key, value in d.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            if isinstance(value, (dict, list)):
                flattened.update(flatten_json(value, new_key, separator, max_depth, depth + 1))
            else:
                flattened[new_key] = value
    elif isinstance(d, list):
        for index, value in enumerate(d):
            new_key = f"{prefix}{separator}{index}" if prefix else str(index)
            if isinstance(value, (dict, list)):
                flattened.update(flatten_json(value, new_key, separator, max_depth, depth + 1))
            else:
                flattened[new_key] = value

    return flattened


class FeedlyFetcher:
    def __init__(self, token, stream_id, article_count):
        self.token = token
        self.stream_id = stream_id
        self.article_count = article_count
        self.url = f'https://feedly.com/v3/streams/contents?streamId={stream_id}&count={article_count}'
        self.headers = {'Authorization': f'Bearer {token}'}

    def fetch_articles(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f'An HTTP error occurred: {e}')
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f'A request error occurred: {e}')
            sys.exit(1)

        try:
            response_dict = response.json()
        except ValueError as e:
            print(f'An error occurred while decoding the JSON response: {e}')
            sys.exit(1)

        return response_dict.get('items', [])


    def process_articles(self, article_list):
        # Flatten heavily nested JSON objects up to a specified depth and create a DataFrame
        max_depth = 3 # Set the maximum depth to flatten
        flattened_articles = [flatten_json(article, max_depth=max_depth) for article in article_list]
        df = pd.DataFrame(flattened_articles)

        return df


    def save_to_csv(self, df):
        if df.empty:
            print('No articles were fetched or processed. Exiting.')
            sys.exit(0)

        try:
            df.to_csv('article_data.csv', index=False)
        except IOError as e:
            print(f'An error occurred while saving the CSV file: {e}')
            sys.exit(1)

        print('Article data has been successfully saved to "article_data.csv"')


def main():
    parser = argparse.ArgumentParser(description='Fetch and save article data from the Feedly API')
    parser.add_argument('--token', required=True, help='Your personal Feedly API key')
    parser.add_argument('--stream_id', required=True, help='The unique identifier for the Feedly stream')
    parser.add_argument('--article_count', type=int, required=True, help='The number of articles to fetch from the Feedly API')

    args = parser.parse_args()

    fetcher = FeedlyFetcher(args.token, args.stream_id, args.article_count)
    articles = fetcher.fetch_articles()
    df = fetcher.process_articles(articles)
    fetcher.save_to_csv(df)


if __name__ == '__main__':
    main()
