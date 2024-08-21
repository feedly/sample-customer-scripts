import argparse
from collections import defaultdict
import requests
from datetime import datetime, timedelta
import pandas as pd

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.feedly.com/v3"

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def get_newsletters():
    print("Fetching newsletters...")
    url = f"{BASE_URL}/newsletters"
    response = requests.get(url, headers=headers)
    newsletters = response.json()
    print(f"Found {len(newsletters)} newsletters")
    return newsletters

def get_newsletter_issues(newsletter_id):
    print(f"Fetching issues for newsletter ID: {newsletter_id}")
    url = f"{BASE_URL}/newsletters/{newsletter_id}/issues"
    response = requests.get(url, headers=headers)
    issues = response.json()
    print(f"Found {len(issues)} issues")
    return issues

def get_issue_preview(newsletter_id, issue_id):
    print(f"Fetching preview for issue ID: {issue_id}")
    url = f"{BASE_URL}/newsletters/{newsletter_id}/issues/{issue_id}/view"
    response = requests.get(url, headers=headers)
    return response.json()

def count_articles(html_content):
    count = html_content.count("Summary.")
    print(f"Found {count} articles in this issue")
    return count

def main(days_to_look_back):
    print("Starting newsletter analysis...")
    look_back_date = datetime.now() - timedelta(days=days_to_look_back)
    print(f"Analyzing newsletters from {look_back_date} onwards")
    data = defaultdict(lambda: {'Article Count': 0, 'Issue Count': 0, 'Latest Timestamp': datetime.min})

    newsletters = get_newsletters()
    
    for i, newsletter in enumerate(newsletters, 1):
        print(f"\nProcessing newsletter {i}/{len(newsletters)}")
        newsletter_id = newsletter['id']
        newsletter_title = newsletter['title']
        print(f"Newsletter: {newsletter_title} (ID: {newsletter_id})")
        
        try:
            issues = get_newsletter_issues(newsletter_id)
            
            for issue in issues:
                sent_at = datetime.fromtimestamp(issue['sentAt'] / 1000)
                print(f"  Issue sent at: {sent_at}")
                
                if sent_at > look_back_date:
                    print(f"  This issue is within the last {days_to_look_back} days. Analyzing...")
                    try:
                        issue_preview = get_issue_preview(newsletter_id, issue['id'])
                        html_content = issue_preview.get('html', '')
                        if not html_content:
                            print("  Warning: No HTML content found in the issue preview.")
                            continue
                        article_count = count_articles(html_content)
                        
                        data[newsletter_id]['Newsletter Title'] = newsletter_title
                        data[newsletter_id]['Article Count'] += article_count
                        data[newsletter_id]['Issue Count'] += 1
                        data[newsletter_id]['Latest Timestamp'] = max(data[newsletter_id]['Latest Timestamp'], sent_at)
                        
                        print(f"  Updated data for {newsletter_title}. Total articles: {data[newsletter_id]['Article Count']}")
                    except Exception as e:
                        print(f"  Error processing issue {issue['id']}: {str(e)}")
                else:
                    print(f"  This issue is older than {days_to_look_back} days. Skipping.")
        except Exception as e:
            print(f"Error processing newsletter {newsletter_id}: {str(e)}")

    print("\nCreating DataFrame and saving to CSV...")
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'Newsletter ID'
    df.reset_index(inplace=True)
    df = df[['Newsletter ID', 'Newsletter Title', 'Article Count', 'Issue Count', 'Latest Timestamp']]
    print(df)
    df.to_csv('newsletter_analysis.csv', index=False)
    print("Analysis complete. Results saved to 'newsletter_analysis.csv'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze newsletters for a specified number of days.")
    parser.add_argument("-d", "--days", type=int, default=7, help="Number of days to look back (default: 7)")
    args = parser.parse_args()

    main(args.days)