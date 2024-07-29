from scripts.feedly_api import Feedly
import json
from scripts.confluence import Confluence_API
from datetime import date
#from catAPI import CatAPI

def main():
    
    # Enter Information here:
    pagename = "Confluence pagename"
    board_streamID = "Board ID"
    
    feedly = Feedly("config.json")
    
    # Get all Articles from the Daily Board
    response = json.loads(feedly.get_board_articles(board_streamID)) 

    # Html content (style is always fixed)
    html_output ='''<style>
        .wrapper {
    padding: 20px 0px 20px;
    width: auto;
    }
    .wrapper .element {
    padding: 10px 10px 10px 10px;
    display: flex;
    flex-direction: row;
    }
    .wrapper .element .text {
    padding-left: 20px;
    }
    .wrapper .element .text .title {
    font-weight: bold;
    font-size: 20px;
    color: #010E52;
    }
    .wrapper .element .text .sources {
    padding: 5px 0px 5px 0px;
    }
    .wrapper .element .text .sources a {
    text-decoration: none !important;
    }
    .wrapper .element .text .moreInf a {
    text-decoration: none !important;
    }/*# sourceMappingURL=main.css.map */
    </style>'''

    for element in response["items"]:
        # Load information from json:
        if "title" in element:
            title = element["title"]
        else:
            title = "missing title" 
        print(title)
        if "visual" in element:
            pic_source = element["visual"]["url"]
        else:
            pic_source = "https://wiki.gematik.de/download/attachments/500279726/Bild.png?version=1&modificationDate=1714055444189&api=v2"
        if "originId" in element:
            source_url = element["originId"]
        else:
            source_url = "unknown" 
        source_name = element["origin"]["title"]

        # Check if leoSummary exists, and concatenate sentences, otherwise use snippet
        if "comment" in element:
            content = element["comment"]
        elif "leoSummary" in element:
            content = "\n".join(sentence["text"] for sentence in element["leoSummary"]["sentences"])
        elif "snippet" in element:
            content = element["snippet"]
        elif "summary" in element:
            content = element["summary"]["content"]
        else:
            content = "something went wrong..."
        feedly_link = "https://feedly.com/i/entry/"+ element["id"]

        # Insert Data in HTML:
        element_html = f'''
        <div class="wrapper">
            <div class="element">
                <div class="picture"><img src="{pic_source}" alt="" width="150px" height="auto"></div>
                <div class="text">
                    <div class="title">{title}</div>
                    <div class="sources"><a href="{source_url}">{source_name}</a></div>
                    <div class="summary">{content}</div>
                    <br>
                    <div class="moreInf"><a href="{feedly_link}">Feedly Entry</a></div>
                </div>
            </div>
        </div>
        '''
        html_output += element_html
    
    # Set up Confluence API
    confluence_api = Confluence_API("confluence_config.json")
    #Find the current Daily page and set the ID
    confluence_api.find_page_id(pagename)
    # Get the current Daily page with the found ID 
    page = confluence_api.get_page()
    # Replace filler with content
    try:
        page['body']['storage']['value'] = page['body']['storage']['value'].replace("<div class=Feedly_placeholder></div>", str(html_output))
    except:
        print("filler not found!")
    # Push to current Daily without printing
    confluence_api.update_page(str(page['body']['storage']['value']), page['title'])

if __name__ == "__main__":
    main()
