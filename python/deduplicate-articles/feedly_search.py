#!/usr/bin/env python3
"""
Feedly API Search with Enhanced Deduplication

This script handles deduplication using:
1. Feedly's native duplicate detection (when available)
2. Title similarity matching to catch duplicates Feedly misses
3. Proper handling of articles without clusters

Requirements:
    pip install requests python-dateutil python-dotenv
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple
import requests
import sys
import os
from dotenv import load_dotenv
import csv
from collections import defaultdict
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeedlySearchClient:
    """Client for searching and deduplicating Feedly articles."""
    
    def __init__(self, api_token: str, db_file: str = None, retention_days: int = 30, dedup_by_cluster: bool = True, title_similarity_threshold: float = 0.85):
        """
        Initialize the Feedly client.
        
        Args:
            api_token: Your Feedly Enterprise API token
            db_file: Path to CSV file for persistent storage
            retention_days: How many days to keep entries in the database
            dedup_by_cluster: If True, keep only one article per story cluster
            title_similarity_threshold: Minimum similarity ratio for title deduplication (0-1)
        """
        self.api_token = api_token
        self.base_url = "https://feedly.com/v3"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        
        # Deduplication tracking
        self.seen_entry_ids: Set[str] = set()
        self.seen_cluster_ids: Set[str] = set()
        self.articles_by_cluster: Dict[str, List[Dict]] = {}
        self.deduplicated_articles: List[Dict] = []
        self.dedup_by_cluster = dedup_by_cluster
        self.title_similarity_threshold = title_similarity_threshold
        
        # Track duplicate groups
        self.duplicate_groups: List[Set[str]] = []
        self.article_to_group: Dict[str, int] = {}
        
        # Track seen titles for similarity matching
        self.seen_titles: List[Tuple[str, str]] = []  # (title, article_id)
        
        # Statistics
        self.stats = {
            "removed_by_similarity": 0,
            "removed_by_cluster": 0,
            "removed_by_previous_seen": 0,
            "removed_by_title_similarity": 0,
            "articles_without_cluster": 0,
            "duplicate_groups_found": 0
        }
        
        # Persistent storage
        self.db_file = db_file
        self.retention_days = retention_days
        
        # Load existing entries from database
        if self.db_file:
            self.load_seen_entries()
    
    def load_seen_entries(self):
        """Load previously seen entry IDs from CSV database."""
        if not os.path.exists(self.db_file):
            logger.info(f"No existing database found at {self.db_file}")
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        entries_loaded = 0
        entries_expired = 0
        
        try:
            with open(self.db_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    seen_date = datetime.fromisoformat(row['seen_date'])
                    if seen_date > cutoff_date:
                        self.seen_entry_ids.add(row['entry_id'])
                        if row.get('cluster_id'):
                            self.seen_cluster_ids.add(row['cluster_id'])
                        entries_loaded += 1
                    else:
                        entries_expired += 1
            
            logger.info(f"Loaded {entries_loaded} entries from database ({entries_expired} expired)")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
    
    def save_seen_entries(self):
        """Save all seen entry IDs to CSV database."""
        if not self.db_file:
            return
        
        # Load existing entries to preserve ones we didn't see this run
        existing_entries = []
        if os.path.exists(self.db_file):
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            try:
                with open(self.db_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        seen_date = datetime.fromisoformat(row['seen_date'])
                        if seen_date > cutoff_date and row['entry_id'] not in self.seen_entry_ids:
                            existing_entries.append(row)
            except Exception as e:
                logger.error(f"Error reading existing database: {e}")
        
        # Write all entries (existing + new)
        try:
            with open(self.db_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['entry_id', 'cluster_id', 'seen_date', 'title']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write existing entries
                writer.writerows(existing_entries)
                
                # Write new entries from this run
                now = datetime.now().isoformat()
                for article in self.deduplicated_articles:
                    writer.writerow({
                        'entry_id': article.get('id', ''),
                        'cluster_id': article.get('cluster_id', ''),
                        'seen_date': now,
                        'title': article.get('title', '')[:200]  # Truncate long titles
                    })
            
            logger.info(f"Saved {len(self.seen_entry_ids)} entries to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def is_title_duplicate(self, title: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a title is too similar to any previously seen title.
        
        Args:
            title: The title to check
            
        Returns:
            Tuple of (is_duplicate, matching_article_id)
        """
        if not title:
            return False, None
        
        title_lower = title.lower().strip()
        
        for seen_title, article_id in self.seen_titles:
            similarity = SequenceMatcher(None, title_lower, seen_title.lower()).ratio()
            if similarity >= self.title_similarity_threshold:
                return True, article_id
        
        return False, None
    
    def build_duplicate_graph(self, articles: List[Dict]):
        """
        Build a graph of duplicate relationships from the articles.
        Creates groups where all connected articles are considered duplicates.
        
        Args:
            articles: List of articles from the API
        """
        # Build adjacency list of duplicate relationships
        duplicate_graph = defaultdict(set)
        article_by_id = {}
        
        for article in articles:
            article_id = article.get('id')
            if not article_id:
                continue
            
            article_by_id[article_id] = article
            
            # Add edges for all duplicates
            duplicates = article.get('duplicates', []) or []
            for dup in duplicates:
                dup_id = dup.get('id') if isinstance(dup, dict) else None
                if dup_id:
                    # Create bidirectional edges
                    duplicate_graph[article_id].add(dup_id)
                    duplicate_graph[dup_id].add(article_id)
        
        # Find connected components (groups of duplicates)
        visited = set()
        
        def dfs(node, group):
            """Depth-first search to find all connected articles."""
            if node in visited:
                return
            visited.add(node)
            group.add(node)
            for neighbor in duplicate_graph[node]:
                dfs(neighbor, group)
        
        # Find all duplicate groups
        for article_id in duplicate_graph:
            if article_id not in visited:
                group = set()
                dfs(article_id, group)
                if len(group) > 1:  # Only track groups with actual duplicates
                    group_id = len(self.duplicate_groups)
                    self.duplicate_groups.append(group)
                    for aid in group:
                        self.article_to_group[aid] = group_id
                    self.stats["duplicate_groups_found"] += 1
        
        logger.info(f"Found {self.stats['duplicate_groups_found']} duplicate groups")
    
    def search_articles(
        self,
        search_query: Dict[str, Any],
        count: int = 100,
        newer_than_days: Optional[int] = 7,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Search for articles using the Feedly API.
        
        Args:
            search_query: The search query in Feedly format
            count: Number of articles per page
            newer_than_days: Only get articles from the last N days
            max_pages: Maximum number of pages to retrieve
            
        Returns:
            List of all retrieved articles (before deduplication)
        """
        url = f"{self.base_url}/search/contents"
        
        # Calculate timestamp for newer_than parameter
        newer_than = None
        if newer_than_days:
            newer_than = int((datetime.now() - timedelta(days=newer_than_days)).timestamp() * 1000)
        
        all_articles = []
        continuation = None
        page = 0
        
        while page < max_pages:
            params = {
                "count": count,
                "similar": "true"  # CRITICAL: This enables duplicate detection
            }
            
            if newer_than:
                params["newerThan"] = newer_than
                
            if continuation:
                params["continuation"] = continuation
            
            try:
                logger.info(f"Fetching page {page + 1}...")
                response = requests.post(
                    url,
                    params=params,
                    headers=self.headers,
                    json=search_query,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    logger.info("No more articles found")
                    break
                
                all_articles.extend(items)
                logger.info(f"Retrieved {len(items)} articles from page {page + 1}")
                
                # Check for continuation token
                continuation = data.get("continuation")
                if not continuation:
                    logger.info("No more pages available")
                    break
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching articles: {e}")
                break
                
        logger.info(f"Total articles retrieved: {len(all_articles)}")
        return all_articles
    
    def deduplicate_articles(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        Deduplicate articles using both similarity and clustering.
        
        Args:
            articles: List of articles from the API
            
        Returns:
            Dictionary containing statistics
        """
        stats = {
            "total_articles": len(articles),
            "unique_articles": 0,
            "duplicates_removed": 0,
            "clusters_found": 0
        }
        
        # First, build the duplicate graph
        self.build_duplicate_graph(articles)
        
        # Track which articles from duplicate groups we've kept
        kept_from_group = {}
        
        for article in articles:
            entry_id = article.get("id")
            
            if not entry_id:
                continue
            
            # Skip if previously seen
            if entry_id in self.seen_entry_ids:
                self.stats["removed_by_previous_seen"] += 1
                stats["duplicates_removed"] += 1
                continue
            
            # Check if this article is part of a duplicate group (from Feedly's detection)
            if entry_id in self.article_to_group:
                group_id = self.article_to_group[entry_id]
                
                # If we've already kept an article from this group, skip this one
                if group_id in kept_from_group:
                    self.stats["removed_by_similarity"] += 1
                    stats["duplicates_removed"] += 1
                    logger.debug(f"Skipping duplicate (group {group_id}): {article.get('title', 'No title')}")
                    continue
                else:
                    # Keep this article as the representative of its group
                    kept_from_group[group_id] = entry_id
                    # Mark all articles in this group as seen
                    for aid in self.duplicate_groups[group_id]:
                        self.seen_entry_ids.add(aid)
            
            # Check for title similarity (catches duplicates Feedly misses)
            title = article.get('title', '')
            if title:
                is_dup, _ = self.is_title_duplicate(title)
                if is_dup:
                    self.stats["removed_by_title_similarity"] += 1
                    stats["duplicates_removed"] += 1
                    logger.debug(f"Skipping title duplicate: {title[:60]}...")
                    continue
            
            # Handle clustering
            featured_meme = article.get("featuredMeme", {})
            cluster_id = featured_meme.get("id") if featured_meme else None
            
            if not cluster_id:
                self.stats["articles_without_cluster"] += 1
            
            # Check if we've already seen this cluster
            if self.dedup_by_cluster and cluster_id and cluster_id in self.seen_cluster_ids:
                self.stats["removed_by_cluster"] += 1
                stats["duplicates_removed"] += 1
                logger.debug(f"Skipping article from already-seen cluster: {cluster_id}")
                continue
            
            # Track this entry
            self.seen_entry_ids.add(entry_id)
            
            # Track the title for future similarity checks
            if title:
                self.seen_titles.append((title, entry_id))
            
            # Track cluster
            if cluster_id:
                if cluster_id not in self.articles_by_cluster:
                    self.articles_by_cluster[cluster_id] = []
                    stats["clusters_found"] += 1
                    if self.dedup_by_cluster:
                        self.seen_cluster_ids.add(cluster_id)
                self.articles_by_cluster[cluster_id].append(article)
                article["cluster_id"] = cluster_id
                article["cluster_label"] = featured_meme.get("label", "Unknown")
            
            # Store duplicate count for reference
            article["duplicate_count"] = len(self.duplicate_groups[self.article_to_group[entry_id]]) - 1 if entry_id in self.article_to_group else 0
            
            # Add to deduplicated list
            self.deduplicated_articles.append(article)
            stats["unique_articles"] += 1
        
        return stats
    
    def get_deduplicated_results(self) -> Dict[str, Any]:
        """
        Get the final deduplicated results with clustering information.
        
        Returns:
            Dictionary containing deduplicated articles and cluster information
        """
        return {
            "deduplicated_articles": self.deduplicated_articles,
            "articles_by_cluster": self.articles_by_cluster,
            "total_unique_articles": len(self.deduplicated_articles),
            "total_clusters": len(self.articles_by_cluster),
            "deduplication_stats": self.stats
        }
    
    def save_results(self, output_file: str, format: str = "json"):
        """
        Save deduplicated results to a file.
        
        Args:
            output_file: Path to output file
            format: Output format ('json' or 'csv')
        """
        results = self.get_deduplicated_results()
        
        if format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_file}")
            
        elif format == "csv":
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if self.deduplicated_articles:
                    # Define CSV fields
                    fieldnames = [
                        'id', 'title', 'published', 'crawled', 'author',
                        'origin_title', 'origin_url', 'url', 'cluster_id',
                        'cluster_label', 'duplicate_count', 'has_cluster', 'summary'
                    ]
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for article in self.deduplicated_articles:
                        row = {
                            'id': article.get('id', ''),
                            'title': article.get('title', ''),
                            'published': datetime.fromtimestamp(
                                article.get('published', 0) / 1000
                            ).isoformat() if article.get('published') else '',
                            'crawled': datetime.fromtimestamp(
                                article.get('crawled', 0) / 1000
                            ).isoformat() if article.get('crawled') else '',
                            'author': article.get('author', ''),
                            'origin_title': article.get('origin', {}).get('title', ''),
                            'origin_url': article.get('origin', {}).get('htmlUrl', ''),
                            'url': article.get('alternate', [{}])[0].get('href', '') if article.get('alternate') else '',
                            'cluster_id': article.get('cluster_id', ''),
                            'cluster_label': article.get('cluster_label', ''),
                            'duplicate_count': article.get('duplicate_count', 0),
                            'has_cluster': 'Yes' if article.get('cluster_id') else 'No',
                            'summary': article.get('summary', {}).get('content', '')[:500]  # Truncate summary
                        }
                        writer.writerow(row)
                        
            logger.info(f"Results saved to {output_file}")


def create_default_search_query() -> Dict[str, Any]:
    """
    Create a default search query for cybersecurity content.
    
    This example searches for Lazarus Group activity with specific malware.
    Modify this based on your needs.
    """
    return {
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


def main():
    """Main function to run the search and deduplication."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    api_token = os.getenv('FEEDLY_API_TOKEN')
    if not api_token:
        logger.error("FEEDLY_API_TOKEN not found in .env file")
        sys.exit(1)
    
    # Parse other configuration values
    query_file = os.getenv('FEEDLY_QUERY_FILE', 'search_query.json')
    output_file = os.getenv('FEEDLY_OUTPUT_FILE', 'feedly_results.json')
    output_format = os.getenv('FEEDLY_OUTPUT_FORMAT', 'json')
    days = int(os.getenv('FEEDLY_SEARCH_DAYS', '7'))
    count = int(os.getenv('FEEDLY_SEARCH_COUNT', '100'))
    max_pages = int(os.getenv('FEEDLY_MAX_PAGES', '5'))
    verbose = os.getenv('FEEDLY_VERBOSE', 'false').lower() == 'true'
    db_file = os.getenv('FEEDLY_DB_FILE', 'feedly_seen_entries.csv')
    retention_days = int(os.getenv('FEEDLY_DB_RETENTION_DAYS', '30'))
    dedup_by_cluster = os.getenv('FEEDLY_DEDUP_BY_CLUSTER', 'true').lower() == 'true'
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load search query
    if query_file:
        try:
            with open(query_file, 'r') as f:
                search_query = json.load(f)
            logger.info(f"Loaded search query from {query_file}")
        except Exception as e:
            logger.error(f"Error loading query file: {e}")
            sys.exit(1)
    else:
        search_query = create_default_search_query()
        logger.info("Using default search query (Lazarus Group)")
    
    # Initialize client
    client = FeedlySearchClient(api_token, db_file=db_file, retention_days=retention_days, dedup_by_cluster=dedup_by_cluster)
    
    # Log deduplication mode
    if dedup_by_cluster:
        logger.info("Cluster-based deduplication is ENABLED - keeping only one article per story")
    else:
        logger.info("Cluster-based deduplication is DISABLED - keeping all articles")
    
    # Search articles
    logger.info("Starting article search...")
    articles = client.search_articles(
        search_query=search_query,
        count=count,
        newer_than_days=days,
        max_pages=max_pages
    )
    
    if not articles:
        logger.warning("No articles found")
        sys.exit(0)
    
    # Deduplicate
    logger.info("Deduplicating articles...")
    stats = client.deduplicate_articles(articles)
    
    # Print statistics
    logger.info("=" * 50)
    logger.info("DEDUPLICATION STATISTICS:")
    logger.info(f"  Total articles retrieved: {stats['total_articles']}")
    logger.info(f"  Unique articles: {stats['unique_articles']}")
    logger.info(f"  Duplicates removed: {stats['duplicates_removed']}")
    logger.info(f"  Story clusters found: {stats['clusters_found']}")
    logger.info("")
    logger.info("BREAKDOWN BY METHOD:")
    logger.info(f"  Removed by Feedly duplicates field: {client.stats['removed_by_similarity']}")
    logger.info(f"  Removed by title similarity: {client.stats['removed_by_title_similarity']}")
    logger.info(f"  Removed by cluster deduplication: {client.stats['removed_by_cluster']}")
    logger.info(f"  Removed by previous database entries: {client.stats['removed_by_previous_seen']}")
    logger.info(f"  Articles without clusters: {client.stats['articles_without_cluster']}")
    logger.info(f"  Duplicate groups found (Feedly): {client.stats['duplicate_groups_found']}")
    logger.info("=" * 50)
    
    # Save results
    client.save_results(output_file, format=output_format)
    
    # Save seen entries to database
    client.save_seen_entries()
    
    # Print sample of clusters
    results = client.get_deduplicated_results()
    if results['articles_by_cluster']:
        logger.info("\nTop story clusters:")
        for _, cluster_articles in list(results['articles_by_cluster'].items())[:5]:
            if cluster_articles:
                logger.info(f"  - {cluster_articles[0].get('cluster_label', 'Unknown')}: {len(cluster_articles)} articles")
    
    # Provide insight about articles without clusters
    if client.stats['articles_without_cluster'] > 0:
        percentage = (client.stats['articles_without_cluster'] / stats['unique_articles']) * 100 if stats['unique_articles'] > 0 else 0
        logger.info(f"\nNOTE: {client.stats['articles_without_cluster']} unique articles ({percentage:.1f}%) don't have clusters.")
        logger.info("These articles were deduplicated using Feedly's similarity detection (duplicates field).")
        if client.stats['duplicate_groups_found'] > 0:
            logger.info(f"Found and processed {client.stats['duplicate_groups_found']} groups of similar articles.")


if __name__ == "__main__":
    main()