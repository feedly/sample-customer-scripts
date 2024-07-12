import sys
import time
import requests
import csv
import re
import html
from collections import defaultdict
from datetime import datetime

def flatten_json(d, prefix='', separator='_', max_depth=5, depth=0):
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

def fetch_articles(token, stream_id, article_count, fetch_all=False, last_timestamp=None):
    url = f'https://feedly.com/v3/streams/contents?streamId={stream_id}&count={article_count}'
    headers = {'Authorization': f'Bearer {token}'}
    all_articles = []
    continuation = None

    while True:
        params = {'count': article_count}
        if last_timestamp is not None:
            params['newerThan'] = last_timestamp
        if continuation is not None:
            params['continuation'] = continuation

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_dict = response.json()

        all_articles.extend(response_dict.get('items', []))
        continuation = response_dict.get('continuation')
        print(f'Retrieved {len(all_articles)} articles')
        if not fetch_all or continuation is None:
            break

    return all_articles

def clean_text(text):
    # Decode HTML entities
    text = html.unescape(text)
    # Remove any remaining non-printable characters
    return ''.join(char for char in text if char.isprintable())

def epoch_to_date(epoch_ms):
    return datetime.fromtimestamp(epoch_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def save_to_csv(article_list, columns=None):
    if not article_list:
        print('No articles were fetched or processed. Exiting.')
        sys.exit(0)

    # Remove duplicates based on 'id' and 'title'
    unique_articles = {}
    for article in article_list:
        article_id = article['id']
        article_title = clean_text(article.get('title', ''))
        
        # Use both id and title as a composite key for deduplication
        key = (article_id, article_title)
        
        if key not in unique_articles:
            unique_articles[key] = article

    flattened_articles = [flatten_json(article) for article in unique_articles.values()]
    fieldnames = columns if columns else sorted(list(set().union(*(article.keys() for article in flattened_articles))))

    with open('article_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in flattened_articles:
            row = {k: article.get(k, '') for k in fieldnames}
            
            # Clean the title
            if 'title' in row:
                row['title'] = clean_text(row['title'])
            
            # Convert epoch time to readable date
            if 'published' in row:
                row['published'] = epoch_to_date(int(row['published']))

            # Convert epoch time to readable date
            if 'crawled' in row:
                row['crawled'] = epoch_to_date(int(row['crawled']))
            
            writer.writerow(row)

    print(f'Article data has been successfully saved to "article_data.csv"')
    print(f'Total articles after deduplication: {len(unique_articles)}')

def get_all_columns(token, stream_id):
    sample_articles = fetch_articles(token, stream_id, article_count=10, fetch_all=False)
    flattened_articles = [flatten_json(article) for article in sample_articles]
    all_columns = sorted(list(set().union(*(article.keys() for article in flattened_articles))))
    
    # Group columns
    column_groups = defaultdict(list)
    for column in all_columns:
        parts = column.split('_')
        if len(parts) > 1:
            group = parts[0]
            column_groups[group].append(column)
        else:
            column_groups['general'].append(column)
    
    return column_groups

def print_columns(column_groups):
    print("Available columns:")
    for group, columns in column_groups.items():
        print(f"\n{group.capitalize()} fields:")
        
        # Sort columns to ensure consistent output
        sorted_columns = sorted(columns)
        
        if group == 'general':
            # Print all general fields
            for column in sorted_columns:
                print(f"  - {column}")
        else:
            # Print only the first 10 columns for non-general fields
            for column in sorted_columns[:10]:
                print(f"  - {column}")
            
            # If there are more than 10 columns, indicate this
            if len(sorted_columns) > 10:
                print(f"  ... and {len(sorted_columns) - 10} more")

        # Print a summary of the structure
        structure = summarize_structure(sorted_columns)
        print(f"  Structure: {structure}")


def summarize_structure(columns):
    if not columns:
        return "No fields"
    
    # Get the common prefix
    common_prefix = columns[0].split('_')[0]
    
    # Check if all columns have numbered suffixes
    numbered = all(re.match(rf"{common_prefix}_\d+", col) for col in columns)
    
    if numbered:
        max_number = max(int(col.split('_')[1]) for col in columns)
        return f"{common_prefix}_0 to {common_prefix}_{max_number}"
    else:
        # List unique suffixes
        suffixes = set('_'.join(col.split('_')[1:]) for col in columns)
        return f"{common_prefix}_[{', '.join(sorted(suffixes))}]"

def main():
    # Hardcoded values (change based on your requirements)
    token = 'YOUR_FEEDLY_TOKEN'
    stream_id = 'YOUR_STREAM_ID'
    article_count = 100
    fetch_all = True
    hours_ago = 24
    columns = ['id', 'title', 'origin_title', 'alternate_0_href', 'published', 'crawled', 'author', 'sources_0_title', 'sources_1_title', 'leoSummary_sentences_0_text', 'leoSummary_sentences_1_text']

    if len(sys.argv) > 1 and sys.argv[1] == '--columns':
        column_groups = get_all_columns(token, stream_id)
        print_columns(column_groups)
        sys.exit(0)

    last_timestamp = int(time.time() * 1000) - (hours_ago * 3600 * 1000)

    all_articles = fetch_articles(token, stream_id, article_count, fetch_all=fetch_all, last_timestamp=last_timestamp)
    save_to_csv(all_articles, columns)

if __name__ == '__main__':
    main()

