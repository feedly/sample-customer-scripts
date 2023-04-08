import argparse
import sys
import time
import requests
import csv
import json
from time import sleep

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
        """
        Initialize a FeedlyFetcher instance with the provided arguments.

        :param token: The personal Feedly API key.
        :param stream_id: The unique identifier for the Feedly stream.
        :param article_count: The number of articles to fetch from the Feedly API.
        """
        self.token = token
        self.stream_id = stream_id
        self.article_count = article_count
        self.url = f'https://feedly.com/v3/streams/contents?streamId={stream_id}&count={article_count}'
        self.headers = {'Authorization': f'Bearer {token}'}

    def fetch_articles(self, last_timestamp=None, continuation=None):
        """
        Fetch articles from the Feedly API using the provided token, stream_id, and article_count.

        :return: A list of fetched articles as JSON objects (dictionaries).
        """
        params = {'count': self.article_count}
        if last_timestamp is not None:
            params['newerThan'] = last_timestamp
        if continuation is not None:
            params['continuation'] = continuation
        
        try:
            response = requests.get(self.url, headers=self.headers, params=params)
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

    def get_continuation(self):
        """
        Get the continuation value from the Feedly API response.

        :return: The continuation value as a string or None if not present.
        """
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

        return response_dict.get('continuation')

    def save_to_csv(self, article_list, max_depth, columns):
        """
        Save the provided article_list as a flattened CSV file with specified columns.

        :param article_list: A list of fetched articles as JSON objects (dictionaries).
        :param max_depth: The maximum JSON depth to flatten when saving to CSV.
        :param columns: A list of columns to include in the output CSV.
        """
        if not article_list:
            print('No articles were fetched or processed. Exiting.')
            sys.exit(0)

        flattened_articles = [flatten_json(article, max_depth=max_depth) for article in article_list]

        # Use the specified columns if provided, otherwise include all columns
        fieldnames = columns if columns else sorted(list(set().union(*(article.keys() for article in flattened_articles))))

        try:
            with open('article_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for article in flattened_articles:
                    writer.writerow({k: article[k] for k in fieldnames if k in article})
        except IOError as e:
            print(f'An error occurred while saving the CSV file: {e}')
            sys.exit(1)

        print('Article data has been successfully saved to "article_data.csv"')

    def save_to_json(self, article_list):
        """
        Save the provided article_list as a JSON file.

        :param article_list: A list of fetched articles as JSON objects (dictionaries).
        """        
        if not article_list:
            print('No articles were fetched. Exiting.')
            sys.exit(0)

        try:
            with open('article_data.json', 'w', encoding='utf-8') as jsonfile:
                json.dump(article_list, jsonfile, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f'An error occurred while saving the JSON file: {e}')
            sys.exit(1)

        print('Article data has been successfully saved to "article_data.json"')

    def fetch_all_articles(self, last_timestamp=None):
        """
        Fetch all available articles from the Feedly API using the provided token, stream_id, and continuation.

        :return: A list of fetched articles as JSON objects (dictionaries).
        """
        all_articles = []
        continuation = None
        new_articles = []

        while True:
            params = {'streamId': self.stream_id, 'count': self.article_count}
            if last_timestamp is not None:
                params['newerThan'] = last_timestamp
            if continuation is not None:
                params['continuation'] = continuation

            try:
                response = requests.get(self.url, headers=self.headers, params=params)
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

            new_articles.extend(response_dict.get('items', []))
            continuation = response_dict.get('continuation')
            print(f'Retrieved {len(new_articles)} articles')  # Added print statement

            if continuation is None:
                break

        all_articles.extend(new_articles)
        return all_articles


def main():
    parser = argparse.ArgumentParser(description='Fetch and save article data from the Feedly API')
    parser.add_argument('--token', required=True, help='Your personal Feedly API key')
    parser.add_argument('--stream_id', required=True, help='The unique identifier for the Feedly stream')
    parser.add_argument('--article_count', type=int, default=100, help='The number of articles to fetch from the Feedly API per request (default: 100)')
    parser.add_argument('--fetch_all', action='store_true', help='Fetch all articles available in the stream. If this option is not specified, fetch articles based on --article_count.')
    parser.add_argument('--hours_ago', type=int, help='Number of hours ago to fetch articles from. (e.g., 12 for articles published in the past 12 hours)')
    parser.add_argument('--output_format', choices=['csv', 'json'], default='csv', help='The output format for the saved file (default: csv)')
    parser.add_argument('--max_depth', type=int, default=3, help='The maximum JSON depth to flatten when saving to CSV (default: 3)')
    parser.add_argument('--columns', nargs='*', default=['id', 'title', 'origin_title', 'originId', 'published', 'author', 'unread', 'leoSummary_sentences_0_text', 'leoSummary_sentences_1_text'], help='The list of columns to include in the output (default: id, title, published, originId, author, etc.)')

    args = parser.parse_args()

    fetcher = FeedlyFetcher(args.token, args.stream_id, args.article_count)

    if args.fetch_all:
        all_articles = fetcher.fetch_all_articles()
    elif args.hours_ago:
        hours_ago_ms = args.hours_ago * 3600 * 1000
        last_timestamp = int(time.time() * 1000) - hours_ago_ms
        all_articles = fetcher.fetch_all_articles(last_timestamp=last_timestamp)
    else:
        all_articles = fetcher.fetch_articles()

    if args.output_format == 'csv':
        flattened_articles = [flatten_json(article, max_depth=args.max_depth) for article in all_articles]
        fetcher.save_to_csv(flattened_articles, args.max_depth, args.columns)
    elif args.output_format == 'json':
        fetcher.save_to_json(all_articles)

if __name__ == '__main__':
    main()
