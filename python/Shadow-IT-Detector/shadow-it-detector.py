"""
Shadow IT Package Detector
Detects calls to PyPI (Python) and npm (JavaScript) package repositories
Usage: python simple_repo_detector.py logfile.csv

Note: This template currently monitors PyPI and npm repositories only. 
To monitor additional package ecosystems, add their domains to REPO_DOMAINS 
and implement corresponding package extraction functions.

Additional repository domains you may want to monitor:
- Maven Central: repo1.maven.org, central.maven.org, search.maven.org
- RubyGems: rubygems.org, gem-server.com
- Packagist (Composer/PHP): packagist.org, repo.packagist.org
- NuGet (.NET): nuget.org, api.nuget.org
- Go Modules: proxy.golang.org, sum.golang.org
- Cargo (Rust): crates.io, index.crates.io
- CPAN (Perl): cpan.org, metacpan.org
- Hex (Elixir): hex.pm, repo.hex.pm
- CocoaPods (iOS): cdn.cocoapods.org, trunk.cocoapods.org
- Pub (Dart/Flutter): pub.dev, pub.dartlang.org
- CRAN (R): cran.r-project.org, cloud.r-project.org
- Hackage (Haskell): hackage.haskell.org
- Clojars (Clojure): clojars.org, repo.clojars.org
- Swift Package Manager: github.com (Swift packages)
- Conda: conda.anaconda.org, repo.anaconda.com
"""

import csv
import json
import re
import sys
from urllib.parse import urlparse

# Repository domains to monitor
REPO_DOMAINS = {
    # Python Package Index
    'pypi.org': 'PyPI',
    'files.pythonhosted.org': 'PyPI',
    'upload.pypi.org': 'PyPI',

    # NPM Registry
    'registry.npmjs.org': 'npm',
    'npmjs.com': 'npm',
    'www.npmjs.com': 'npm'
}


def extract_domain(url_or_host):
    """Extract domain from URL or hostname"""
    if not url_or_host:
        return None

    # If it looks like a URL, parse it
    if '://' in url_or_host:
        try:
            domain = urlparse(url_or_host).netloc
        except:
            domain = url_or_host
    else:
        domain = url_or_host

    # Remove port if present
    domain = domain.split(':')[0].lower()
    return domain


def extract_python_packages(url, command):
    """Extract Python package names from URLs and pip commands"""
    packages = []

    # From URL patterns like /simple/requests/ or /project/requests/
    if url:
        # PyPI simple API: /simple/package-name/
        if '/simple/' in url:
            match = re.search(r'/simple/([^/]+)/?', url, re.I)
            if match:
                packages.append(match.group(1))

        # PyPI project pages: /project/package-name/
        if '/project/' in url:
            match = re.search(r'/project/([^/]+)/?', url, re.I)
            if match:
                packages.append(match.group(1))

    # From pip install commands
    if command:
        pip_match = re.search(r'pip\s+install\s+([^\n;|]+)', command, re.I)
        if pip_match:
            args = pip_match.group(1).split()
            for arg in args:
                if not arg.startswith('-') and not arg.endswith('.txt'):
                    # Handle package==version format
                    pkg_name = arg.split('==')[0].strip()
                    if pkg_name:
                        packages.append(pkg_name)

    return list(set(packages))  # Remove duplicates


def extract_npm_packages(url, command):
    """Extract npm package names from URLs and npm commands"""
    packages = []

    # From registry URLs like /package-name or /@scope/package-name
    if url:
        path = urlparse(url).path if '://' in url else url
        # Get first path segment after /
        parts = [p for p in path.split('/') if p and not p.startswith('-')]
        if parts:
            # Handle URL encoding like @scope%2Fpackage
            pkg_name = parts[0].replace('%2F', '/')
            packages.append(pkg_name)

    # From npm install commands
    if command:
        npm_match = re.search(r'npm\s+(?:install|i)\s+([^\n;|]+)', command, re.I)
        if npm_match:
            args = npm_match.group(1).split()
            for arg in args:
                if not arg.startswith('-'):
                    # Handle package@version format
                    if '@' in arg and not arg.startswith('@'):
                        pkg_name = arg.split('@')[0].strip()
                    else:
                        pkg_name = arg.strip()
                    if pkg_name:
                        packages.append(pkg_name)

    return list(set(packages))


def analyze_log_entry(entry):
    """Analyze a single log entry for repository calls"""
    # Get relevant fields (flexible field names)
    url = entry.get('url') or entry.get('request') or entry.get('uri') or ''
    host = entry.get('host') or entry.get('sni') or entry.get('server_name') or ''
    command = entry.get('command_line') or entry.get('process') or entry.get('cmd') or ''
    user = entry.get('user') or entry.get('username') or ''
    timestamp = entry.get('timestamp') or entry.get('time') or ''

    # Extract domain from URL if host is empty
    if not host and url:
        host = extract_domain(url)
    else:
        host = extract_domain(host)

    # Check if this is a repository domain
    repo_type = None
    for domain, repo in REPO_DOMAINS.items():
        if host and (host == domain or host.endswith('.' + domain)):
            repo_type = repo
            break

    # Extract packages based on repository type
    packages = []
    if repo_type == 'PyPI':
        packages = extract_python_packages(url, command)
    elif repo_type == 'npm':
        packages = extract_npm_packages(url, command)

    # Also check commands even if no repo domain detected
    if not packages:
        packages.extend(extract_python_packages(url, command))
        packages.extend(extract_npm_packages(url, command))
        packages = list(set(packages))

    # Return finding if we detected something interesting
    if repo_type or packages:
        return {
            'timestamp': timestamp,
            'user': user,
            'host': host,
            'url': url,
            'repository': repo_type or 'Unknown',
            'packages': packages,
            'command': command[:100] + '...' if len(command) > 100 else command
        }

    return None


def process_log_file(filename):
    """Process a CSV log file and detect repository calls"""
    findings = []

    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            # Auto-detect delimiter
            sample = f.read(1024)
            f.seek(0)

            delimiter = ','
            if sample.count('\t') > sample.count(','):
                delimiter = '\t'

            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, 1):
                finding = analyze_log_entry(row)
                if finding:
                    finding['row'] = row_num
                    findings.append(finding)

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return []

    return findings


def save_results(findings, output_file='repo_findings.csv'):
    """Save findings to CSV file"""
    if not findings:
        print("No repository calls detected.")
        return

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'user', 'repository', 'host', 'packages', 'url', 'command']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for finding in findings:
            writer.writerow({
                'timestamp': finding.get('timestamp', ''),
                'user': finding.get('user', ''),
                'repository': finding.get('repository', ''),
                'host': finding.get('host', ''),
                'packages': '; '.join(finding.get('packages', [])),
                'url': finding.get('url', ''),
                'command': finding.get('command', '')
            })

    print(f"Results saved to {output_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_repo_detector.py <logfile.csv>")
        print("\nExpected CSV columns (any subset):")
        print("- timestamp, user, host, url, command_line")
        print("- Alternative names: time/ts, username, sni/server_name, request/uri, process/cmd")
        sys.exit(1)

    log_file = sys.argv[1]
    print(f"Analyzing {log_file}...")

    findings = process_log_file(log_file)

    if findings:
        print(f"\nFound {len(findings)} repository calls:")

        # Summary by repository
        repo_counts = {}
        package_counts = {}

        for finding in findings:
            repo = finding.get('repository', 'Unknown')
            repo_counts[repo] = repo_counts.get(repo, 0) + 1

            for pkg in finding.get('packages', []):
                package_counts[pkg] = package_counts.get(pkg, 0) + 1

        print("\nRepository breakdown:")
        for repo, count in repo_counts.items():
            print(f"  {repo}: {count} calls")

        print(f"\nTop packages accessed:")
        sorted_packages = sorted(package_counts.items(), key=lambda x: x[1], reverse=True)
        for pkg, count in sorted_packages[:10]:
            print(f"  {pkg}: {count} times")

        save_results(findings)

    else:
        print("No repository calls detected in the log file.")


# For testing - modify this section to use your test file
if __name__ == "__main__":
    # Temporary test configuration
    import sys
    # Add the destination path to the csv, if required
    sys.argv = ["os-pack-detection.py", "network_traffic_converted.csv"]
    main()
