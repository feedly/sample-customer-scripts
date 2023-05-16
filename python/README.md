# Feedly API Article Fetcher

This Python script allows you to fetch and save article data from the Feedly API. It supports saving article data in CSV and JSON formats.

## Requirements

1. Python 3.6 or later.
2. Python libraries: argparse, requests, json, and csv. You can install them using pip:

```
pip install argparse requests
```

## Getting Started

1. Obtain your personal Feedly API token. For instructions, please visit: [Feedly API Guides](https://feedly.notion.site/Feedly-API-Guides-a8794499f1144f6bb4db4aa363ab5fbd).
2. Find the unique identifier for the Feedly stream (stream_id) you want to fetch articles from.

## How to Run

To run the script, open a command prompt or terminal and navigate to the directory containing the script. Execute the following command:

```
python feedly_fetcher.py --token YOUR_API_TOKEN --stream_id YOUR_STREAM_ID
```

Replace `YOUR_API_TOKEN` and `YOUR_STREAM_ID` with your actual Feedly API token and stream ID, respectively.

By default, the script fetches 100 articles and saves them as a CSV file named "article_data.csv". You can change the behavior using optional arguments.

## Optional Arguments

- `--article_count N`: Fetch N articles per request (default: 100).
- `--fetch_all`: Fetch all available articles in the stream.
- `--hours_ago H`: Fetch articles published in the past H hours.
- `--output_format FORMAT`: Specify the output format for the saved file (csv or json, default: csv).
- `--max_depth D`: Set the maximum JSON depth to flatten when saving to CSV (default: 3).
- `--columns COLUMN1 COLUMN2 ...`: List the columns to include in the output (default: id, title, origin_title, originId, published, author, unread, leoSummary_sentences_0_text, leoSummary_sentences_1_text).

Example command:

```
python feedly_fetcher.py --token YOUR_API_TOKEN --stream_id YOUR_STREAM_ID --article_count 50 --fetch_all --hours_ago 12 --output_format json
```

This command fetches all articles published in the past 12 hours, with a maximum of 50 articles per request, and saves them as a JSON file.

For more information on the command line arguments, run:

```
python feedly_fetcher.py --help
```

## Output

The script will generate a file named "article_data.csv" or "article_data.json" in the same directory as the script, containing the fetched article data.
