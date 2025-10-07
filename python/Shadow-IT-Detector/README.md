# Simple Shadow IT Package Detector

A Python script for analysing network logs to detect open source package installations and identify shadow IT dependencies in your organisation.

## Overview

This tool processes network traffic logs to identify calls to package repositories (PyPI, npm, Github etc.) and extract information about packages being installed by developers. It helps security teams gain visibility into open source dependencies that may not be officially tracked or approved.

## Features

- Detects calls to PyPI (Python) and npm (JavaScript) package repositories
- Extracts package names from URLs and command-line arguments
- Supports multiple log formats (CSV, JSONL)
- Generates detailed reports with package usage statistics
- Flexible field mapping for different log schemas

## Requirements

- Python 3.6 or higher
- Standard library modules only (no external dependencies)

## Installation

No installation required. Simply download `simple_repo_detector.py` and run it with Python 3.

## Usage

### Basic Usage

```bash
python3 simple_repo_detector.py logfile.csv

```

### Supported Input Formats

**CSV Format** (recommended):

```
timestamp,user,host,url,command_line
2024-01-15T10:30:00Z,jsmith,pypi.org,https://pypi.org/simple/requests/,
2024-01-15T10:31:00Z,jsmith,,,pip install requests==2.31.0

```

**JSONL Format**:

```json
{"timestamp": "2024-01-15T10:30:00Z", "user": "jsmith", "host": "pypi.org", "url": "https://pypi.org/simple/requests/"}
{"timestamp": "2024-01-15T10:31:00Z", "user": "jsmith", "command_line": "pip install requests==2.31.0"}

```

### Expected Log Fields

The script looks for these fields (alternative names accepted):

- **timestamp** (or time, ts): When the request occurred
- **user** (or username): User making the request
- **host** (or sni, server_name): Target hostname
- **url** (or request, uri): Full URL requested
- **command_line** (or process, cmd): Command executed

Missing fields are handled gracefully - the script will work with any subset of available fields.

## Output

The script generates two output files:

1. **repo_findings.csv**: Summary report with one row per finding
2. **repo_findings.jsonl**: Detailed findings in JSON format

### Sample Output

```
Analyzing logfile.csv...

Found 3 repository calls:

Repository breakdown:
  PyPI: 2 calls
  npm: 1 calls

Top packages accessed:
  requests: 2 times
  lodash: 1 times

Results saved to repo_findings.csv

```

## Extending for Other Repositories

This template monitors PyPI and npm by default. To add support for other package ecosystems:

1. Add repository domains to the `REPO_DOMAINS` dictionary
2. Implement package extraction functions for the new repository type
3. Add extraction logic to `analyze_log_entry()`

### Additional Repository Domains

Consider monitoring these repositories for comprehensive coverage:

- **GitHub:** github.com, raw.githubusercontent.com, api.github.com
- **Maven Central**: repo1.maven.org, central.maven.org, search.maven.org
- **RubyGems**: rubygems.org, gem-server.com
- **Packagist (PHP)**: packagist.org, repo.packagist.org
- **NuGet (.NET)**: nuget.org, api.nuget.org
- **Go Modules**: proxy.golang.org, sum.golang.org
- **Cargo (Rust)**: crates.io, index.crates.io
- **CPAN (Perl)**: cpan.org, metacpan.org
- **Hex (Elixir)**: hex.pm, repo.hex.pm
- **CocoaPods (iOS)**: cdn.cocoapods.org, trunk.cocoapods.org
- **Pub (Dart/Flutter)**: pub.dev, pub.dartlang.org
- **CRAN (R)**: cran.r-project.org, cloud.r-project.org

## Data Collection Methods

This script processes logs from various network monitoring approaches:

- Proxy logs (Squid, nginx)
- DNS query logs (dnsmasq, Pi-hole)
- Network packet captures (tcpdump, Wireshark)
- System monitoring tools (osquery, auditd)
- Firewall logs (pfctl, iptables)

## Security Considerations

- The script processes log data only - it does not perform active network monitoring
- Sensitive information in URLs or commands may be logged - review output before sharing
- Consider data retention policies for monitoring logs
- Ensure compliance with employee privacy policies

## Troubleshooting

**No results found:**

- Verify log format matches expected fields
- Check that repository domains are included in monitoring
- Ensure timestamp format is recognised

**Partial results:**

- Review field mapping - alternative column names may not be detected
- Check for URL encoding in captured URLs
- Verify command-line arguments are fully captured

**Performance with large files:**

- The script processes files line by line for memory efficiency
- For very large logs (>1GB), consider splitting files or filtering by date range

## Example Integration

```python
# Basic usage in your own scripts
from simple_repo_detector import process_log_file, analyze_records

# Process a log file
findings = process_log_file("network_logs.csv")

# Analyze pre-loaded records
records = [{"url": "https://pypi.org/simple/requests/", "user": "dev1"}]
findings = analyze_records(records)

```

## License

This script is provided as-is for educational and security assessment purposes. Modify and distribute freely while maintaining attribution. Ensure compliance with your organisation's security policies and Feedly's API terms of service.
