# Feedly API Search with Enhanced Deduplication

This script searches the Feedly API and removes duplicate articles using multiple detection methods to ensure the cleanest possible results.

## Problem Solved

When using Feedly's API with `similar=true`, some duplicate articles may still appear in results because:
- Not all articles have a `featuredMeme` (cluster ID)  
- Articles from different sources may have very similar content
- Articles without clusters can't be deduplicated by cluster

## Solution

This script combines multiple deduplication methods:
1. **Feedly's native duplicate detection** - Uses the `duplicates` field when available
2. **Cluster-based deduplication** - Groups articles about the same story (when cluster exists)
3. **Title similarity matching** - Catches near-identical titles (85% similarity threshold)
4. **Persistent tracking** - Remembers previously seen articles across runs

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.sample` to `.env` and update with your settings:

```env
# Required: Your Feedly Enterprise API token
FEEDLY_API_TOKEN=your_token_here

# Optional: Customize these as needed
FEEDLY_QUERY_FILE=search_query.json       # Path to search query JSON
FEEDLY_OUTPUT_FILE=feedly_results.json    # Output filename
FEEDLY_OUTPUT_FORMAT=csv                  # Output format: json or csv
FEEDLY_SEARCH_DAYS=7                      # Days to look back
FEEDLY_SEARCH_COUNT=100                   # Articles per page
FEEDLY_MAX_PAGES=5                        # Maximum pages to fetch
FEEDLY_VERBOSE=false                      # Enable debug logging
FEEDLY_DB_FILE=feedly_seen_entries.csv    # Database for tracking seen articles
FEEDLY_DB_RETENTION_DAYS=30               # Days to remember articles
FEEDLY_DEDUP_BY_CLUSTER=true             # Enable cluster deduplication
```

### 3. Configure Search Query

Edit `search_query.json` to define your search. Example for threat intelligence:

```json
{
    "layers": [
        {
            "parts": [
                {
                    "id": "nlp/f/entity/gz:ta:68391641-859f-4a9a-9a1e-3e5cf71ec376",
                    "label": "Lazarus Group",
                    "type": "threatActor"
                }
            ],
            "type": "matches",
            "salience": "about"
        }
    ],
    "source": {
        "items": [
            {
                "type": "publicationBucket",
                "id": "byf:cybersecurity-bundle",
                "tier": "tier1",
                "label": "Cybersecurity Bundle"
            }
        ]
    }
}
```

## Usage

Simply run the script:

```bash
python feedly_search.py
```

## Output

The script provides detailed statistics showing how duplicates were removed:

```
==================================================
DEDUPLICATION STATISTICS:
  Total articles retrieved: 100
  Unique articles: 78
  Duplicates removed: 22
  Story clusters found: 27

BREAKDOWN BY METHOD:
  Removed by Feedly duplicates field: 0
  Removed by title similarity: 5
  Removed by cluster deduplication: 17
  Removed by previous database entries: 0
  Articles without clusters: 51
  Duplicate groups found (Feedly): 0
==================================================
```

### Output Files

- **CSV format**: Includes columns for id, title, published date, URL, cluster info, and more
- **JSON format**: Full article data with deduplication metadata
- **Database file**: Tracks seen articles to prevent duplicates across runs

## How It Works

1. **Fetches articles** from Feedly API with `similar=true` parameter
2. **Builds duplicate graph** from Feedly's `duplicates` field
3. **Checks title similarity** using 85% threshold (configurable)
4. **Groups by cluster** when available
5. **Tracks seen articles** in persistent database
6. **Outputs deduplicated results** with detailed statistics

## Key Features

- **Handles articles without clusters** - Uses title similarity when cluster ID is missing
- **Persistent deduplication** - Remembers articles across multiple runs
- **Configurable thresholds** - Adjust similarity sensitivity as needed
- **Detailed logging** - See exactly which method removed each duplicate
- **Multiple output formats** - Choose JSON or CSV based on your needs

## Troubleshooting

### Still seeing duplicates?

1. **Lower the title similarity threshold** - Edit the script and change `title_similarity_threshold=0.85` to a lower value like `0.75`
2. **Check if articles have different titles** - Some duplicates may have slightly different titles from different sources
3. **Enable verbose logging** - Set `FEEDLY_VERBOSE=true` to see detailed deduplication decisions

### Performance tips

- **Adjust page count** - Reduce `FEEDLY_MAX_PAGES` if you don't need all results
- **Clear old database** - Delete `feedly_seen_entries.csv` to start fresh
- **Tune retention** - Adjust `FEEDLY_DB_RETENTION_DAYS` based on your needs

## Technical Details

The script enhances deduplication by:
- Building bidirectional duplicate relationships (if A→B, then B→A)
- Using fuzzy string matching for titles (difflib.SequenceMatcher)
- Maintaining a sliding window of seen articles (default 30 days)
- Combining multiple signals for comprehensive deduplication

## Support

For issues or questions about the Feedly API:
- Check the deduplication statistics to understand what's happening
- Enable verbose logging for detailed debugging
- Adjust the title similarity threshold if needed
- Consider that some duplicates may be intentional (different perspectives on same story)
