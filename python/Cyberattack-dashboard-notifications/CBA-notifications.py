import requests
import sqlite3
import json
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Set config function
def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from a YAML file and validate required fields."""
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        # Define required fields
        required_fields = {
            "feedly": ["api_key", "api_config"],
            "database": ["path"],
            "slack": ["bot_token", "channel"],
            "gmail": ["sender_email", "sender_password", "recipient_email"]
        }

        # Validate required sections and keys
        for section, keys in required_fields.items():
            if section not in config:
                raise ValueError(f"Missing required section '{section}' in config.yaml")
            for key in keys:
                if key not in config[section]:
                    raise ValueError(f"Missing key '{key}' under '{section}' in config.yaml")

        return config

    except FileNotFoundError:
        print("Error: Configuration file not found.")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        raise
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
        raise


# Validate and create Database
class CyberAttackTracker:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the tracker with configuration settings."""
        self.db_path = config["database"]["path"]  # Database path from config

        self.api_key = config["feedly"]["api_key"]  # Feedly API Key
        self.api_config = config["feedly"]["api_config"]  # Feedly API query configuration

        self.slack_bot_token = config["slack"]["bot_token"]  # Slack Bot Token
        self.slack_channel = config["slack"]["channel"]  # Slack Channel ID
        self.slack_client = WebClient(token=self.slack_bot_token)  # Initialize Slack client

        self.base_url = "https://api.feedly.com/v3/ml/relationships/cyber-attacks/dashboard/table"  # Cyber attacks API URL
        self.current_run_time = datetime.utcnow()  # Store script execution time
        self.config = config  # Store full configuration

        self.setup_logging()  # Set up logging
        self.init_database()  # Initialize database

    # Set up logging messages
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    # Initialise the database storing cyber attacks from Cyber Attack Dashboard
    def init_database(self):
        db_exists = os.path.exists(self.db_path)
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute('''
                CREATE TABLE IF NOT EXISTS cyber_attacks (
                    id TEXT PRIMARY KEY,
                    short_overview TEXT,
                    threat_actors TEXT,
                    malware_families TEXT,
                    victim_label TEXT,
                    attack_date TEXT,
                    what_description TEXT,
                    so_what TEXT,
                    data JSON,
                    last_updated TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS change_log (
                    id TEXT,
                    changed_at TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    change_type TEXT,
                    FOREIGN KEY (id) REFERENCES cyber_attacks (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS script_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

        if not db_exists:
            self.logger.info(f"Created new database at {self.db_path}")
        else:
            self.logger.info(f"Connected to existing database at {self.db_path}")

    def fetch_cyber_attacks(self) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.base_url, json=self.api_config, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed {str(e)}")
            return {}

    def extract_threat_actors(self, threat_actors: List[Dict]) -> str:
        """Extract threat actor labels from the threat actors array."""
        if not threat_actors:
            return "Unknown"
        return ", ".join([ta.get("entity", {}).get("label", "Unknown") for ta in threat_actors])

    def extract_malware_families(self, malware_families: List[Dict]) -> str:
        """Extract malware family labels from the malware families array."""
        if not malware_families:
            return "Unknown"
        return ", ".join([mf.get("entity", {}).get("label", "Unknown") for mf in malware_families])

    def process_cyber_attacks(self):
        # Fetch cyber attacks and detect changes
        attacks_data = self.fetch_cyber_attacks()
        attacks = attacks_data.get('attacks', [])

        if not attacks:
            self.logger.info("No cyber attacks found.")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        notifications = []

        for attack in attacks:
            attack_id = attack["id"]
            short_overview = attack.get("shortOverview", "No title available")
            threat_actors = self.extract_threat_actors(attack.get("threatActors", []))
            malware_families = self.extract_malware_families(attack.get("malwareFamilies", []))
            victim_label = attack.get("victim", {}).get("label", "Unknown victim")
            attack_date = attack.get("attackDate", "Unknown date")
            what_description = attack.get("what", "No description available")
            so_what = attack.get("soWhat", "No impact description available")

            attack_data = json.dumps(attack)
            cursor.execute("SELECT data FROM cyber_attacks WHERE id = ?", (attack_id,))
            result = cursor.fetchone()

            if result:
                old_data = json.loads(result[0])
                if old_data != attack:
                    cursor.execute('''
                        UPDATE cyber_attacks
                        SET short_overview = ?, threat_actors = ?, malware_families = ?, 
                            victim_label = ?, attack_date = ?, what_description = ?, 
                            so_what = ?, data = ?, last_updated = ?
                        WHERE id = ?
                    ''', (short_overview, threat_actors, malware_families, victim_label,
                          attack_date, what_description, so_what, attack_data,
                          self.current_run_time.isoformat(), attack_id))

                    self.logger.info(f"Updated cyber attack: {short_overview}")
                    self.send_slack_notification(attack, "updated")
                    notifications.append((attack, "updated"))

            else:
                cursor.execute('''
                    INSERT INTO cyber_attacks (id, short_overview, threat_actors, malware_families, 
                                             victim_label, attack_date, what_description, so_what, 
                                             data, last_updated) 
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                ''', (attack_id, short_overview, threat_actors, malware_families, victim_label,
                      attack_date, what_description, so_what, attack_data,
                      self.current_run_time.isoformat()))

                self.logger.info(f"New cyber attack found: {short_overview}")
                self.send_slack_notification(attack, "new")
                notifications.append((attack, "new"))

        conn.commit()
        conn.close()

        if notifications:
            self.send_email_notification(notifications)

    def send_slack_notification(self, attack_data: Dict[str, Any], change_type: str):
        """Send a notification to Slack when a new or updated cyber attack is found."""
        short_overview = attack_data.get("shortOverview", "No title available")
        threat_actors = self.extract_threat_actors(attack_data.get("threatActors", []))
        malware_families = self.extract_malware_families(attack_data.get("malwareFamilies", []))
        victim_label = attack_data.get("victim", {}).get("label", "Unknown victim")
        attack_date = attack_data.get("attackDate", "Unknown date")
        what_description = attack_data.get("what", "No description available")
        so_what = attack_data.get("soWhat", "No impact description available")

        message = (
            f"*{change_type.upper()} Cyber Attack Alert*\n"
            f"> *Attack:* {short_overview}\n"
            f"> *Victim:* {victim_label}\n"
            f"> *Threat Actor(s):* {threat_actors}\n"
            f"> *Malware:* {malware_families}\n"
            f"> *Attack Date:* {attack_date}\n"
            f"> *What:* {what_description}\n"
            f"> *Impact:* {so_what}"
        )

        try:
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=message,
                parse="mrkdwn"
            )
            if response["ok"]:
                self.logger.info(f"Sent Slack notification for {short_overview}")
            else:
                self.logger.error(f"Failed to send Slack message: {response['error']}")

        except SlackApiError as e:
            self.logger.error(f"Slack API Error: {str(e)}")

    def send_email_notification(self, notifications: List[tuple]):
        sender = self.config["gmail"]["sender_email"]
        password = self.config["gmail"]["sender_password"]
        recipient = self.config["gmail"]["recipient_email"]

        # Separate new and updated attacks
        new_attacks = [attack for attack, change_type in notifications if change_type == "new"]
        updated_attacks = [attack for attack, change_type in notifications if change_type == "updated"]

        subject = f"Cyber Attack Digest: {len(new_attacks)} new, {len(updated_attacks)} updated attacks"

        body = "<h1>Cyber Attack Dashboard Digest</h1><br>"

        # New Cyber Attacks Section
        if new_attacks:
            body += "<h2>New Cyber Attacks</h2>"
            for attack in new_attacks:
                short_overview = attack.get("shortOverview", "No title available")
                threat_actors = self.extract_threat_actors(attack.get("threatActors", []))
                malware_families = self.extract_malware_families(attack.get("malwareFamilies", []))
                victim_label = attack.get("victim", {}).get("label", "Unknown victim")
                attack_date = attack.get("attackDate", "Unknown date")
                what_description = attack.get("what", "No description available")
                so_what = attack.get("soWhat", "No impact description available")
                victim_description = attack.get("victim", {}).get("description", "No victim description available")

                body += f"""
        <div style="margin-bottom: 20px; padding: 10px; border-left: 4px solid #ff4444;">
        <p><strong>Attack:</strong> {short_overview}</p>
        <p><strong>Victim:</strong> {victim_label}</p>
        <p><strong>Victim Description:</strong> {victim_description}</p>
        <p><strong>Threat Actor(s):</strong> {threat_actors}</p>
        <p><strong>Malware:</strong> {malware_families}</p>
        <p><strong>Attack Date:</strong> {attack_date}</p>
        <p><strong>What:</strong> {what_description}</p>
        <p><strong>So What (Impact):</strong> {so_what}</p>
        </div>
        """

        # Updated Cyber Attacks Section
        if updated_attacks:
            body += "<h2>Updated Cyber Attacks</h2>"
            for attack in updated_attacks:
                short_overview = attack.get("shortOverview", "No title available")
                threat_actors = self.extract_threat_actors(attack.get("threatActors", []))
                malware_families = self.extract_malware_families(attack.get("malwareFamilies", []))
                victim_label = attack.get("victim", {}).get("label", "Unknown victim")
                attack_date = attack.get("attackDate", "Unknown date")
                what_description = attack.get("what", "No description available")
                so_what = attack.get("soWhat", "No impact description available")
                victim_description = attack.get("victim", {}).get("description", "No victim description available")

                body += f"""
        <div style="margin-bottom: 20px; padding: 10px; border-left: 4px solid #ffaa00;">
        <p><strong>Attack:</strong> {short_overview}</p>
        <p><strong>Victim:</strong> {victim_label}</p>
        <p><strong>Victim Description:</strong> {victim_description}</p>
        <p><strong>Threat Actor(s):</strong> {threat_actors}</p>
        <p><strong>Malware:</strong> {malware_families}</p>
        <p><strong>Attack Date:</strong> {attack_date}</p>
        <p><strong>What:</strong> {what_description}</p>
        <p><strong>So What (Impact):</strong> {so_what}</p>
        </div>
        """

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipient
        message['Subject'] = subject
        message.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender, password)
                server.send_message(message)
                self.logger.info("Sent email digest")
        except Exception as e:
            self.logger.error(f"Failed to send email digest: {str(e)}")


def main():
    try:
        config = load_config()
        tracker = CyberAttackTracker(config)
        tracker.logger.info("Cyber attack tracker initialized successfully")
        tracker.process_cyber_attacks()
    except Exception as e:
        logging.error(f"Error initializing cyber attack tracker: {str(e)}")
        raise


if __name__ == "__main__":
    main()
