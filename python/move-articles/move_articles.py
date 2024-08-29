from feedly_api import Feedly
import json


def main():
    # origin Board
    board_streamID = ""
    # target Board
    archive_streamID = ""

    feedly = Feedly("config.json")
    response = json.loads(feedly.get_board_articles(board_streamID)) 
    for element in response["items"]:
        articleID = element["id"]
        # move Article to target Board
        feedly.add_article_board(archive_streamID, articleID)
        # remove from origin Board
        feedly.remove_board_element(board_streamID, articleID)

        
if __name__ == "__main__":
    main()