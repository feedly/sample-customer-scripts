import urllib.parse
import requests
import json
import urllib

def read_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

class Feedly:
    def __init__(self, config, proxies = None):
        self.apikey = (read_config(config))["apiToken"]
        self.proxies = proxies
        self.headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "Authorization": "Bearer " + self.apikey
                }
        
    def get_trending_cves(self):
        url = "https://api.feedly.com/v3/memes/vulnerabilities/en"
        response = requests.get(url, headers=self.headers , proxies=self.proxies)
        return response.text

    def get_trending_threat_actors(self):
        url = "https://api.feedly.com/v3/trends/threat-actors"
        response = requests.get(url, headers=self.headers, proxies=self.proxies)
        return response.text
    
    def get_board_articles(self, streamID):
        url = "https://api.feedly.com/v3/streams/contents?streamID="+ streamID 
        print(url)
        response = requests.get(url, headers=self.headers, proxies=self.proxies)
        return response.text
    
    def remove_board_element(self, streamID, elementID):
        streamID = urllib.parse.quote(streamID, safe= '')
        elementID = urllib.parse.quote(elementID, safe= '')
        url = "https://api.feedly.com/v3/tags/"+ streamID +"/"+ elementID
        response = requests.delete(url, headers=self.headers)
        return response.text
    
    def add_article_board(self, streamID, elementID):
        streamID = urllib.parse.quote(streamID, safe= '')
        url = "https://api.feedly.com/v3/tags/"+ streamID
        payload = elementID
        response = requests.put(url, json=payload, headers=self.headers)
        return response.text