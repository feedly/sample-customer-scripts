import sys
import time
import requests
import csv
import json
import pymysql
import configparser



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

    def save_to_mysql(self, article_list, host, user, password, database_name, table_name, columns):
        if not article_list:
            print('No articles were fetched. Exiting.')
            sys.exit(0)

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database_name
        )

        cursor = connection.cursor()

        flattened_articles = [flatten_json(article) for article in article_list]

        # Filter out unwanted keys based on the column names specified in the config file.
        flattened_articles = [
            {key: article[key] for key in columns if key in article}
            for article in flattened_articles
        ]

        column_names_types = [
            f"`{column_name}` TEXT"
            for column_name in columns
        ]
        create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(column_names_types)}) ROW_FORMAT=DYNAMIC;"
        cursor.execute(create_table_query)
        connection.commit()

        # Now we insert the data
        for article in flattened_articles:
            column_names = ', '.join(f"`{column_name}`" for column_name in article.keys())
            insert_query = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({', '.join(['%s'] * len(article))});"
            cursor.execute(insert_query, tuple(article.values()))

        connection.commit()
        print('Article data has been successfully saved to MySQL')


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    feedly_config = config['Feedly']
    mysql_config = config['MySQL']

    token = feedly_config.get('token')
    stream_id = feedly_config.get('stream_id')
    article_count = feedly_config.getint('article_count', fallback=100)
    fetch_all = feedly_config.getboolean('fetch_all', fallback=False)
    hours_ago = feedly_config.getint('hours_ago', fallback=None)
    output_format = feedly_config.get('output_format', fallback='csv')
    max_depth = feedly_config.getint('max_depth', fallback=3)
    columns = [column.strip() for column in feedly_config.get('columns', fallback='').split(',')]

    fetcher = FeedlyFetcher(token, stream_id, article_count)
    last_timestamp = None

    if hours_ago:
        hours_ago_ms = hours_ago * 3600 * 1000
        last_timestamp = int(time.time() * 1000) - hours_ago_ms

    all_articles = fetcher.fetch_articles(fetch_all=fetch_all, last_timestamp=last_timestamp)

    if output_format == 'csv':
        fetcher.save_to_csv(all_articles, max_depth, columns)
    elif output_format == 'json':
        fetcher.save_to_json(all_articles)
    elif output_format == 'sql':
        fetcher.save_to_mysql(
            all_articles, 
            mysql_config['host'],
            mysql_config['user'],
            mysql_config['password'],
            mysql_config['database'],
            mysql_config['table'],
            columns  # Pass the columns from the config here.
        )


if __name__ == '__main__':
    main()
