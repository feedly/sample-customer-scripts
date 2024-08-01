# Feedly to Wazuh Integration

This project integrates Feedly's threat intelligence data with Wazuh.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Data in Wazuh](#data-in-wazuh)
6. [Benefits and Use Cases](#benefits-and-use-cases)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.7+
- Wazuh manager (version 4.0+)
- Feedly Enterprise account with API access

## Installation

You have two options for installing the script:

### Option 1: Download Single Script

1. Navigate to the repository on GitHub.
2. Find the file `feedly_to_wazuh.py`.
3. Click on the file to view its contents.
4. Click the "Raw" button to view the raw file.
5. Right-click and select "Save As" to download the file to your local machine.

### Option 2: Clone Entire Repository

If you want to clone the entire repository (useful if you want to contribute or use other scripts):

1. Clone this repository:
   ```
   git clone https://github.com/feedly/sample-customer-scripts.git
   cd integrations/wazuh
   ```

After obtaining the script through either method, install the required Python packages:

```
pip install requests stix2
```

## Configuration

### Script Configuration

1. Open `feedly_to_wazuh.py` in a text editor.
2. Update the following variables with your information:
   ```python
   FEEDLY_API_KEY = "YOUR_FEEDLY_API_KEY"
   FEEDLY_STREAM_ID = "YOUR_FEEDLY_STREAM_ID"
   WAZUH_API_URL = "https://your-wazuh-manager:55000"
   WAZUH_API_USER = "your-wazuh-api-user"
   WAZUH_API_PASSWORD = "your-wazuh-api-password"
   ```

### Wazuh Configuration

1. Ensure your Wazuh manager is configured to accept API requests. Add the following to your `ossec.conf`:
   ```xml
   <ossec_config>
     <global>
       <jsonout_output>yes</jsonout_output>
       <alerts_log>yes</alerts_log>
       <logall>no</logall>
       <logall_json>no</logall_json>
     </global>
   </ossec_config>
   ```

2. Create a custom rule for Feedly events. Add this to your `local_rules.xml`:
   ```xml
   <group name="feedly,">
     <rule id="100001" level="10">
       <decoded_as>json</decoded_as>
       <field name="integration">feedly</field>
       <description>Feedly indicator detected: $(feedly.name)</description>
     </rule>
   </group>
   ```

3. Restart Wazuh manager:
   ```
   systemctl restart wazuh-manager
   ```

## Usage

Run the script:
```
python feedly_to_wazuh.py
```

Consider setting up a cron job to run this script at regular intervals.

## Data in Wazuh

The script sends data to Wazuh in the following format:

```json
{
  "integration": "feedly",
  "feedly": {
    "name": "8c69830a50fb85d8a794fa46643493b2",
    "type": "indicator",
    "pattern": "[file:hashes.MD5 = '8c69830a50fb85d8a794fa46643493b2']",
    "valid_from": "2024-08-01T18:21:21.686164Z"
  }
}
```

In Wazuh logs (`/var/ossec/logs/alerts/alerts.json`), you'll see entries like:

```json
{
  "timestamp": "2024-08-01T18:30:00.000+0000",
  "rule": {
    "level": 10,
    "description": "Feedly indicator detected: 8c69830a50fb85d8a794fa46643493b2",
    "id": "100001",
    "firedtimes": 1,
    "groups": ["feedly"]
  },
  "agent": {
    "id": "000",
    "name": "wazuh-manager"
  },
  "manager": {
    "name": "wazuh-manager"
  },
  "id": "1659380400.1234567",
  "full_log": "{\"integration\":\"feedly\",\"feedly\":{\"name\":\"8c69830a50fb85d8a794fa46643493b2\",\"type\":\"indicator\",\"pattern\":\"[file:hashes.MD5 = '8c69830a50fb85d8a794fa46643493b2']\",\"valid_from\":\"2024-08-01T18:21:21.686164Z\"}}"
}
```

## Benefits and Use Cases

1. **Threat Intelligence Integration**: Incorporate Feedly's threat intelligence directly into your Wazuh SIEM.

2. **Real-time Alerting**: Generate alerts based on Feedly indicators detected in your environment.

3. **Correlation**: Correlate Feedly indicators with other security events for more comprehensive threat detection.

4. **Automated Response**: Set up active responses in Wazuh based on Feedly indicators.

5. **Threat Hunting**: Use Feedly data for proactive threat hunting across your environment.

6. **Compliance**: Demonstrate active monitoring and response to potential threats.

7. **Historical Analysis**: Create a historical record of indicators for post-incident analysis and trend tracking.

## Troubleshooting

- Ensure all API keys and credentials are correct.
- Check Wazuh manager logs for any errors: `/var/ossec/logs/ossec.log`
- Verify that the Wazuh API is accessible from the machine running the script.
- If indicators are not appearing in Wazuh, check the script's output for any error messages.

For further assistance, please open an issue in this repository.
