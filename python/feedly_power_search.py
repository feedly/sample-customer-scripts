
import requests
import argparse
import json

class FeedlyPowerSearch:
    def __init__(self, token, query_file_path, article_count=100, days_ago=None, verbose=False):
        self.token = token
        with open(query_file_path, 'r') as file:
            self.query_body = json.load(file)
        self.article_count = article_count
        self.url = 'https://feedly.com/v3/search/contents'
        self.headers = {'Authorization': f'Bearer {token}'}
        self.days_ago = days_ago
        self.verbose = verbose

    def search_articles(self):
        all_articles = []
        continuation = None

        while True:
            params = {'count': self.article_count}
            
            # Convert days to milliseconds for newerThan parameter
            if self.days_ago is not None:
                milliseconds = self.days_ago * 24 * 60 * 60 * 1000
                params['newerThan'] = milliseconds

            if continuation is not None:
                params['continuation'] = continuation

            response = requests.post(self.url, headers=self.headers, params=params, json=self.query_body)
            if response.status_code != 200:
                print("Error occurred while fetching articles. Please check your token and query.")
                return []

            response_dict = response.json()
            all_articles.extend(response_dict.get('items', []))
            continuation = response_dict.get('continuation')
            
            # Print verbose feedback if verbose mode is enabled
            if self.verbose:
                print(f"Fetched {len(all_articles)} articles")
 
            if continuation is None:
                break

        return all_articles

def export_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Search articles on Feedly and export the results to JSON.')
    parser.add_argument('--token', help='Your Feedly Enterprise Token.', required=True)
    parser.add_argument('--query_file', help='Path to the JSON query file for the search payload.', required=True)
    parser.add_argument('-o', '--output', default="output.json", help='Output filename. Default is output.json.')
    parser.add_argument('-d', '--days_ago', type=int, help='Number of days ago to set the newerThan parameter. Converts days to milliseconds.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode for detailed feedback.')

    # Parse the arguments
    args = parser.parse_args()

    searcher = FeedlyPowerSearch(args.token, args.query_file, days_ago=args.days_ago, verbose=args.verbose)
    articles = searcher.search_articles()

    if articles:
        print(f"Found {len(articles)} articles!")
        export_to_json(articles, args.output)
        print(f"Results exported to {args.output}!")
    else:
        print("No articles found.")
