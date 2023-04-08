import argparse
import sys
import time
import requests
import csv
import json

def flatten_json(d, prefix='', separator='_', max_depth=None, depth=0):
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

    def fetch_articles(self, fetch_all=False, last_timestamp=None):
        all_articles = []
        continuation = None

        while True:
            params = {'count': self.article_count}
            if last_timestamp is not None:
                params['newerThan'] = last_timestamp
            if continuation is not None:
                params['continuation'] = continuation

            response = requests.get(self.url, headers=self.headers, params=params)
            response.raise_for_status()
            response_dict = response.json()

            all_articles.extend(response_dict.get('items', []))
            continuation = response_dict.get('continuation')
            print(f'Retrieved {len(all_articles)} articles')
            if not fetch_all or continuation is None:
                break

        return all_articles

    def save_to_csv(self, article_list, max_depth, columns):
        if not article_list:
            print('No articles were fetched or processed. Exiting.')
            sys.exit(0)

        flattened_articles = (flatten_json(article, max_depth=max_depth) for article in article_list)
        fieldnames = columns if columns else sorted(list(set().union(*(article.keys() for article in flattened_articles))))

        with open('article_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for article in flattened_articles:
                writer.writerow({k: article[k] for k in fieldnames if k in article})

        print('Article data has been successfully saved to "article_data.csv"')

    def save_to_json(self, article_list):
        if not article_list:
            print('No articles were fetched. Exiting.')
            sys.exit(0)

        with open('article_data.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(article_list, jsonfile, ensure_ascii=False, indent=2)

        print('Article data has been successfully saved to "article_data.json"')

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
    last_timestamp = None

    if args.hours_ago:
        hours_ago_ms = args.hours_ago * 3600 * 1000
        last_timestamp = int(time.time() * 1000) - hours_ago_ms

    all_articles = fetcher.fetch_articles(fetch_all=args.fetch_all, last_timestamp=last_timestamp)

    if args.output_format == 'csv':
        fetcher.save_to_csv(all_articles, args.max_depth, args.columns)
    elif args.output_format == 'json':
        fetcher.save_to_json(all_articles)

if __name__ == '__main__':
    main()
