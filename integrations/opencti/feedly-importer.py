from pycti import OpenCTIApiClient
from readability import Document
import configparser
import requests
import datetime
import logging
import pytz
import uuid
import json
import re

# Set up the logger
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

config = configparser.ConfigParser()
config.read('config.ini')

# Set config variable for timescope
fetch_since_midnight = config.getboolean('DEFAULT', 'fetch_since_midnight')

# If fetch_since_midnight is True, calculate the datetime for midnight UTC
if fetch_since_midnight:
    now = datetime.datetime.now(tz=pytz.UTC)
    midnight_utc = now.replace(hour=0, minute=0, second=0, microsecond=0)

# Set other config variables
opencti_url = config.get('OpenCTI', 'url')
opencti_api_key = config.get('OpenCTI', 'api_key')
feedly_stream_id = config.get('Feedly', 'stream_id')
feedly_api_key = config.get('Feedly', 'api_key')

# Establish a new OpenCTI API client
opencti_api_client = OpenCTIApiClient(opencti_url, opencti_api_key)

# This variable will keep track of the continuation parameter
continuation = None

# If fetch_since_midnight is True, add the date range parameters
if fetch_since_midnight:
    midnight = int(midnight_utc.timestamp() * 1000)  # Feedly uses milliseconds
    base_url = f'https://feedly.com/v3/enterprise/ioc?streamid={feedly_stream_id}&newerThan={midnight}'
else:
    base_url = f'https://feedly.com/v3/enterprise/ioc?streamid={feedly_stream_id}'

headers = {
  'Authorization': f'Bearer {feedly_api_key}'
}

while True:
    # Add continuation parameter to the URL if it exists
    if continuation is not None:
        url = f"{base_url}&continuation={continuation}"
    else:
        url = base_url

    response = requests.get(url, headers=headers)
    # Check the response status code
    if response.status_code != 200:
        logging.error(f"Error getting data from Feedly: HTTP {response.status_code}")
        break
    # Check that the response data is in the expected format
    try:
        stix_data = response.json()
    except Exception as e:
        logging.error(f"Error parsing JSON data from Feedly: {str(e)}")
        break

    # ### This code block is included for troubleshooting
    # try:
    #     with open('test-data.json', 'r') as f:
    #         stix_data = json.load(f)
    # except FileNotFoundError as e:
    #     logging.error(f"File error occurred: {str(e)}")
    #     break

    # Get the TLP:CLEAR marking definition
    tlp_clear = opencti_api_client.marking_definition.read(filters=[{"key": "definition", "values": ["TLP:CLEAR"]}])

    # Create or get "Feedly Connector" organization
    connector_identity = opencti_api_client.identity.create(
        type='Organization',
        name='Feedly Connector',
        description='Feedly Connector providing information from Feedly.',
    )

    # Initialize lists to separate entities and relationships
    entities = []
    relationships = []

    def create_relationship(source_id, target_id, relationship_type):
        relationship_id = f"relationship--{uuid.uuid4()}"
        return {
            'id': relationship_id,
            'type': 'relationship',
            'relationship_type': relationship_type,
            'source_ref': source_id,
            'target_ref': target_id
        }

    # Iterate over each STIX object in the JSON response
    for stix_object in stix_data["objects"]:
        # Modify the source_name if necessary
        if "external_references" in stix_object:
            for external_reference in stix_object["external_references"]:
                if len(external_reference.get("source_name", "")) <= 2:
                    external_reference["source_name"] = "External report"
        # Modify the properties of all objects
        stix_object["created_by_ref"] = connector_identity['id']
        if "object_marking_refs" in stix_object:
            stix_object["object_marking_refs"].append(tlp_clear["id"])
        else:
            stix_object["object_marking_refs"] = [tlp_clear["id"]]

        # Special handling of indicators
        if stix_object["type"] == "indicator":
            indicator_id = stix_object["id"]
            pattern = stix_object["pattern"]
            # Extract the IOC value from the pattern
            indicator_value = re.search(r"'(.*?)'", pattern).group(1)
            stix_object['name'] = indicator_value

        # Special handling for Report objects
        if stix_object["type"] == "report":
            stix_object["report_types"] = ["feedly-article"]
            # Clean up the description
            doc = Document(stix_object["description"])
            cleaned_description = re.sub('<[^<]+?>', '', doc.summary())
            stix_object["description"] = cleaned_description

            # Create a note object
            note_id = f"note--{uuid.uuid4()}"
            cleaned_description = cleaned_description if len(cleaned_description) >= 2 else "No description available."
            note_object = {
                "type": "note",
                "id": note_id,
                "abstract": "Summary of the report",
                "content": cleaned_description,
                "created_by_ref": stix_object["created_by_ref"],
                "object_marking_refs": stix_object.get("object_marking_refs", []),
                "object_refs": [stix_object["id"]],  # this note is about the report
                "report_types": ["feedly-article"]
            }

        # Add the note to the entities list
        entities.append(note_object)

        # Store the modified object in the entities list
        entities.append(stix_object)

    # Iterate once more to create relationships (since all entities are available)
    for stix_object in stix_data["objects"]:
        try:
            if stix_object["type"] == "report":
            # Add relationship from report to its entities
            # Store related entities by type
                related_entities = {
                    "threat-actor": [],
                    "malware": [],
                    "vulnerability": [],
                    "indicator": [],
                    "attack-pattern": [],
                }
                for entity_id in stix_object.get('object_refs', []):
                    # Fetch the entity
                    entity = next((e for e in entities if e["id"] == entity_id), None)
                    if entity is not None and entity["type"] in related_entities:
                        related_entities[entity["type"]].append(entity_id)

                # Create relationships between entities
                for threat_actor in related_entities["threat-actor"]:
                    for malware in related_entities["malware"]:
                        relationship = create_relationship(threat_actor, malware, 'uses')
                        relationships.append(relationship)
                        stix_object.setdefault('object_refs', []).append(relationship['id'])

                    for vulnerability in related_entities["vulnerability"]:
                        relationship = create_relationship(threat_actor, vulnerability, 'targets')
                        relationships.append(relationship)
                        stix_object.setdefault('object_refs', []).append(relationship['id'])

                    for indicator in related_entities["indicator"]:
                        relationship = create_relationship(indicator, threat_actor, 'indicates')
                        relationships.append(relationship)
                        stix_object.setdefault('object_refs', []).append(relationship['id'])

                    for attack_pattern in related_entities["attack-pattern"]:
                        relationship = create_relationship(threat_actor, attack_pattern, 'uses')
                        relationships.append(relationship)
                        stix_object.setdefault('object_refs', []).append(relationship['id'])

                for malware in related_entities["malware"]:
                    for indicator in related_entities["indicator"]:
                        relationship = create_relationship(indicator, malware, 'indicates')
                        relationships.append(relationship)
                        stix_object.setdefault('object_refs', []).append(relationship['id'])
        except Exception as e:
            logging.error(f"Error processing STIX object {stix_object['id']}: {str(e)}")
            continue

    # Combine entities and relationships into the final bundle
    stix_bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": entities + relationships,
    }

    # Import the modified STIX data into OpenCTI
    try:
        opencti_api_client.stix2.import_bundle(stix_bundle, update=True)
    except Exception as e:
        logging.error(f"Error importing STIX bundle into OpenCTI: {str(e)}")
        continue

    # Check for continuation to retrieve more results
    if 'continuation' in stix_data:
        continuation = stix_data['continuation']
    else:
        break