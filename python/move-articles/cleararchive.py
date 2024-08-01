from feedly_api import Feedly
import json


def main():
    #Archive Board
    archive_streamID = ""

    feedly = Feedly("config.json")
    #Get all Articles from Board
    response = json.loads(feedly.get_board_articles(archive_streamID)) 
    #Go through Articles
    for element in response["items"]:
        articleID = element["id"]
        #remove from origin
        feedly.remove_board_element(archive_streamID, articleID)

        
if __name__ == "__main__":
    main()