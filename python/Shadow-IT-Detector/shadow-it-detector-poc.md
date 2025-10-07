# Shadow IT Package Detection: A Complete Implementation Guide

**⚠️ Security Warning ⚠️**: This proof-of-concept involves installing software packages and monitoring network traffic, which could introduce security risks to your system. We strongly recommend running this implementation in a secure, isolated environment such as a virtual machine or dedicated testing server rather than on your primary workstation or production environment.

## Introduction

This guide demonstrates how to monitor network traffic to open source package repositories and identify developer package installations. We'll use **`osquery`** for system monitoring, `dnsmasq` for DNS query logging, and `tcpdump` for network packet capture to generate traffic data. The captured data is then processed using a custom Python script built with `urllib.parse` and `regex` modules to extract package names from repository URLs and command-line arguments. The implementation provides real-time visibility into PyPI (Python) and npm (JavaScript) package installations, creating an automated inventory of open source dependencies in your environment.

## Software Components Overview

This implementation uses several key tools, each serving a specific purpose in the monitoring pipeline:

**Terminal/Command Line Interface**: The primary interface for configuring and running monitoring tools on macOS systems.

**Homebrew**: macOS package manager that simplifies installation of open source software and monitoring tools.

**osquery**: SQL-based operating system instrumentation framework that can monitor processes, network connections, and system events in real-time.

**dnsmasq**: Lightweight DNS forwarder and DHCP server that provides DNS query logging capabilities for monitoring repository domain requests.

**tcpdump**: Built-in macOS packet capture utility for monitoring network traffic at the packet level.

**simple_repo_detector.py**: Custom Python script (provided separately) that processes network logs and extracts open source package usage patterns.

## Step-by-Step Implementation

### Prerequisites Setup

Begin by ensuring Homebrew is installed on your macOS system. Open Terminal and verify installation:

```bash
brew --version
```

If Homebrew is not installed, install it using:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Core Monitoring Setup

Install osquery for system-level monitoring:

```bash
brew install osquery
```

Install dnsmasq for DNS query monitoring:

```bash
brew install dnsmasq
```

Create the osquery configuration directory:

```bash
sudo mkdir -p /var/osquery
```

Configure osquery to monitor package manager processes. Create the configuration file:

```bash
sudo touch /var/osquery/osquery.conf
```

Add the monitoring configuration:

```bash
echo '{
  "queries": {
    "package_installs": {
      "query": "SELECT datetime(time,'\''unixepoch'\'') as timestamp, username, cmdline as command_line, name as process FROM processes WHERE (cmdline LIKE '\''%pip install%'\'' OR cmdline LIKE '\''%npm install%'\'') AND cmdline NOT LIKE '\''%osquery%'\'';",
      "interval": 30
    }
  }
}' | sudo tee /var/osquery/osquery.conf > /dev/null
```

### DNS Monitoring Configuration

Create dnsmasq configuration directory:

```bash
sudo mkdir -p /opt/homebrew/var/log
```

Configure dnsmasq for DNS query logging:

```bash
echo '# Enable query logging
log-queries
log-facility=/opt/homebrew/var/log/dnsmasq.log

# Forward DNS requests to Google DNS
server=8.8.8.8
server=8.8.4.4

# Listen on localhost
listen-address=127.0.0.1' | sudo tee /opt/homebrew/etc/dnsmasq.conf > /dev/null
```

Start the dnsmasq service:

```bash
brew services start dnsmasq
```

### Traffic Monitoring Activation

Test osquery functionality:

```bash
sudo /usr/local/bin/osqueryi --config_path=/var/osquery/osquery.conf
```

In the osquery shell, verify process monitoring:

```sql
SELECT name, cmdline FROM processes WHERE cmdline LIKE '%python%' LIMIT 3;
```

Exit osquery:

```sql
.quit
```

### Data Collection Process

To collect actual monitoring data, perform package installations while monitoring is active. The system will capture both DNS queries and process execution data.

Install a test package to generate monitoring data:

```bash
pip3 install requests
```

The monitoring systems will automatically log this activity for analysis.

### Analysis and Reporting

Execute the provided detection script on your collected data:

```bash
python3 simple_repo_detector.py your_log_file.csv
```

The script will output a comprehensive analysis including:

- Total number of repository calls detected
- Breakdown by repository type (PyPI, npm, etc.)
- Most frequently accessed packages
- Detailed CSV report of all findings

## Alternative Methods for Troubleshooting

If you encounter issues with the primary dnsmasq approach, several alternative methods can provide similar monitoring capabilities.

**Direct Network Packet Capture**: Use tcpdump to monitor HTTP/HTTPS traffic to repository domains:

```bash
sudo tcpdump -i any -n host pypi.org or host files.pythonhosted.org | tee network_traffic.log
```

**Process Monitoring**: Monitor running processes for package manager activity:

```bash
lsof -i | grep -E "(pypi|npm)" > package_connections.log
```

**Manual Log Conversion**: If automated logging fails, manually create CSV entries from observed network activity:

```bash
echo "timestamp,user,host,url,command_line" > manual_log.csv
echo "2024-09-27T10:30:00Z,username,pypi.org,https://pypi.org/simple/package/,pip install package" >> manual_log.csv
```

These alternative approaches provide flexibility when primary monitoring methods encounter system-specific configuration issues or permission restrictions.

## Implementation Notes

This monitoring approach provides comprehensive visibility into open source package usage without requiring changes to development workflows or tools. The system operates transparently, capturing actual usage patterns that reflect real-world dependency management practices.

The detection script processes various log formats and can identify packages from both URL patterns and command-line arguments, ensuring robust coverage across different installation methods and repository configurations.

Regular execution of this monitoring system will build a comprehensive inventory of your organisation's actual open source dependencies, enabling more accurate threat modelling and proactive security management.
