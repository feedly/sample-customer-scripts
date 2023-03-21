# Description: This script fetches article data from the Feedly API, processes it,
# and saves it as a CSV file.
#
# Input: The script requires the following command-line arguments:
#   --token: Your personal Feedly API key.
#   --stream_id: The unique identifier for the Feedly stream.
#   --article_count: The number of articles to fetch from the Feedly API.
#
# Output: The script outputs a CSV file called "article_data.csv" containing
# the processed article data.
#
# Dependencies: This script requires the following Python libraries:
#   - requests: Used to send HTTP requests to the Feedly API.
#   - pandas: Used to process and store the article data as a DataFrame,
#             and to save the data as a CSV file.
#
# To install pip (Python package manager) if you don't have it, visit:
# https://pip.pypa.io/en/stable/installation/
#
# To set up a virtual environment, follow these steps:
# 1. Install the virtualenv package: pip install virtualenv
# 2. Create a virtual environment in your project folder: python -m virtualenv venv
# 3. Activate the virtual environment:
#    - On Windows: venv\Scripts\activate
#    - On macOS/Linux: source venv/bin/activate
#
# To install dependencies in the virtual environment, run:
# pip install requests pandas
#
# Example usage:
# python feedly_fetcher.py --token YOUR_API_KEY --stream_id YOUR_STREAM_ID --article_count 3

import requests
import pandas as pd
import sys
import argparse


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
            print(f"An HTTP error occurred: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"A request error occurred: {e}")
            sys.exit(1)

        try:
            response_dict = response.json()
        except ValueError as e:
            print(f"An error occurred while decoding the JSON response: {e}")
            sys.exit(1)

        return response_dict.get('items', [])

    def process_articles(self, article_list):
        # Use a list comprehension to normalize JSON objects, and then concatenate them into a single DataFrame
        return pd.concat([pd.json_normalize(article) for article in article_list], ignore_index=True)

    def save_to_csv(self, df):
        if df.empty:
            print("No articles were fetched or processed. Exiting.")
            sys.exit(0)

        try:
            df.to_csv('article_data.csv', index=False)
        except IOError as e:
            print(f"An error occurred while saving the CSV file: {e}")
            sys.exit(1)

        print("Article data has been successfully saved to 'article_data.csv'")


def main():
    parser = argparse.ArgumentParser(description="Fetch and save article data from the Feedly API")
    parser.add_argument('--token', required=True, help='Your personal Feedly API key')
    parser.add_argument('--stream_id', required=True, help='The unique identifier for the Feedly stream')
    parser.add_argument('--article_count', type=int, required=True, help='The number of articles to fetch from the Feedly API')

    args = parser.parse_args()

    fetcher = FeedlyFetcher(args.token, args.stream_id, args.article_count)
    articles = fetcher.fetch_articles()
    df = fetcher.process_articles(articles)
    fetcher.save_to_csv(df)


if __name__ == "__main__":
    main()