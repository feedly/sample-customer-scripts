# Cyber Attack Dashboard Notification System

A Python-based monitoring system that tracks cyber attack intelligence from Feedly's Cyber Attack Dashboard API and provides automated notifications via Slack and/or email when new attacks are detected or existing attacks are updated.
## Features

- **Real-time Monitoring**: Continuously monitors Feedly's cyber attack dashboard for new threat intelligence
- **Change Detection**: Uses SQLite database to identify new attacks and updates to existing attacks
- **Multi-channel Notifications**: 
  - Instant Slack alerts for individual attacks
  - Organized email digests grouping new and updated attacks
- **Comprehensive Data Extraction**: Captures key threat intelligence fields including:
  - Attack overview and title
  - Threat actors involved
  - Malware families used
  - Victim organization details
  - Attack dates and timelines
  - Impact assessments ("What" and "So What")

## Prerequisites

- Python 3.7 or higher
- Feedly API access token
- Slack workspace with bot permissions
- Gmail account with app-specific password

## Installation

1. **Clone or download the script files**:
   - `cyber_attack_tracker.py` (main script)
   - `config.yaml` (configuration file)

2. **Install required Python packages**:
   ```bash
   pip install requests sqlite3 pyyaml slack-sdk
   ```

## Configuration

### 1. Feedly API Setup

1. Obtain your Feedly API token from your Feedly account
2. Configure your dashboard query by:
   - Visiting the [Feedly Cyber Attack Dashboard](https://feedly.com/i/dashboard/cyberAttack)
   - Setting up your desired filters (time period, regions, attack types, etc.)
   - Clicking the "API" button to get the JSON query structure
   - Copying the generated JSON into the `api_config` section of `config.yaml`

### 2. Slack Bot Setup

**Create a Slack Bot**:
1. Visit https://api.slack.com/apps
2. Click 'Create new app' → 'from scratch'
3. Name the app and select your workspace
4. Navigate to 'OAuth & Permissions' in the left sidebar
5. Under "Bot Token Scopes", add these permissions:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`

**Install & Configure Bot**:
1. Click "Install to workspace"
2. Review permissions and click "Allow"
3. Copy the Bot User OAuth Token (starts with `xoxb-`)
4. Store this token securely in your password manager

**Get Channel ID**:
1. Navigate to your desired Slack channel
2. Right-click on the channel name → 'Copy link'
3. Extract the channel ID from the URL (the part after the last slash)

### 3. Gmail Configuration

1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use this app-specific password in the configuration

### 4. Update config.yaml

Replace the placeholder values in `config.yaml`:

```yaml
# Feedly Configuration
feedly:
  api_key: "YOUR_FEEDLY_API_TOKEN"
  api_config:
    {
      "period": {
        "type": "Last7Days",
        "label": "Last 7 Days"
      },
      "layers": [
        {
          "filters": [
            {
              "field": "victimCountry",
              "value": "GB"
            }
          ]
        }
      ]
    }

# Database Configuration
database:
  path: "cyber_attacks.db"

# Slack Configuration
slack:
  bot_token: "YOUR_SLACK_BOT_TOKEN"
  channel: "YOUR_CHANNEL_ID"

# Gmail Configuration
gmail:
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-specific-password"
  recipient_email: "recipient@example.com"
```

## Usage

### Running the Script

Execute the script manually:
```bash
python cyber_attack_tracker.py
```

### Automated Execution

For continuous monitoring, set up a cron job (Linux/macOS) or Task Scheduler (Windows):

**Example cron job (runs every hour)**:
```bash
0 * * * * /usr/bin/python3 /path/to/cyber_attack_tracker.py
```

**Example Windows Task Scheduler**:
- Create a new task that runs `python cyber_attack_tracker.py`
- Set trigger for desired frequency (e.g., hourly)

## Output Format

### Slack Notifications
Individual alerts sent immediately for each new or updated attack:
```
NEW Cyber Attack Alert
> Attack: Ransomware Group Targets Healthcare Provider
> Victim: Regional Medical Center
> Threat Actor(s): BlackCat
> Malware: BlackCat Ransomware
> Attack Date: 2025-09-11
> What: Ransomware encryption of patient databases
> Impact: Potential patient data exposure and service disruption
```

### Email Digest
Organized summary with grouped sections:
```
Cyber Attack Dashboard Digest

New Cyber Attacks
├── Attack 1 with full details
├── Attack 2 with full details
└── Attack 3 with full details

Updated Cyber Attacks
├── Updated Attack 1 with full details
└── Updated Attack 2 with full details
```

## Database Schema

The script creates a SQLite database with the following structure:

- **cyber_attacks**: Main table storing attack data
- **change_log**: Tracks changes over time
- **script_metadata**: Stores script execution metadata

## Customization

### API Query Filters
Modify the `api_config` section in `config.yaml` to change:
- Time periods (`Last24Hours`, `Last7Days`, `Last30Days`, etc.)
- Geographic filters (`victimCountry`, `victimContinent`)
- Attack types (`attackType`)
- Industry filters (`victimIndustry`)
- Threat actor filters (`threatActor`)

### Notification Frequency
Adjust how often the script runs based on your monitoring needs:
- High-frequency: Every 15-30 minutes for critical monitoring
- Standard: Every 1-2 hours for regular awareness
- Low-frequency: Daily for periodic updates

### Data Fields
The script tracks these key fields by default:
- `shortOverview` - Attack title/summary
- `threatActors` - Threat groups involved
- `malwareFamilies` - Malware used in attacks
- `victim` - Target organization information
- `attackDate` - When the attack occurred
- `what` - Description of what happened
- `soWhat` - Impact assessment

## Troubleshooting

### Common Issues

**API Authentication Errors (401)**:
- Verify your Feedly API token is correct
- Check if your token has expired

**Slack Notification Failures**:
- Confirm bot token is valid
- Verify bot has been added to the target channel
- Check bot permissions include `chat:write`

**Email Delivery Issues**:
- Ensure you're using an app-specific password, not your regular Gmail password
- Check that 2-factor authentication is enabled
- Verify sender email configuration

**Database Errors**:
- Check file permissions in the database directory
- Ensure sufficient disk space
- Verify SQLite3 is properly installed

### Logging
The script provides detailed logging to help diagnose issues:
- INFO: Normal operation messages
- ERROR: Failed operations requiring attention

Check the console output or redirect to a log file:
```bash
python cyber_attack_tracker.py >> tracker.log 2>&1
```

## Security Considerations

- Store API tokens and passwords securely
- Use environment variables for sensitive data in production
- Regularly rotate API tokens and passwords
- Monitor for unauthorized access to your notification channels
- Keep dependencies updated for security patches

## Contributing

To extend functionality:
1. Add new notification channels by creating additional methods
2. Extend data extraction by modifying the processing methods
3. Add new filters by updating the configuration structure
4. Enhance analytics by expanding the database schema

## License

This script is provided as-is for cybersecurity monitoring purposes. Ensure compliance with your organization's security policies and Feedly's API terms of service.
