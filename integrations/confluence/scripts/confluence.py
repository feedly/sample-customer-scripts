from atlassian import Confluence
import json

class Confluence_API:
    def __init__(self, confluence_config) -> None:
        input_file = open (confluence_config)
        c = json.load(input_file)
        self.confluenceURL=c["confluence"]
        self.confluenceUser=c["user"]
        self.confluencePass=c["password"]
        self.confluenceSpace=c["space"]
        self.confluence = Confluence(url=self.confluenceURL,username=self.confluenceUser,token=self.confluencePass, cloud=False)
    
    def find_page_id(self, page_name):
        status=self.confluence.get_space(self.confluenceSpace, expand='description.plain,homepage')    
        if "statusCode" in status:
            if status["statusCode"] == 404:
                print("Space not found: " + self.confluenceSpace)
            else:
                print("Unknown error: " + status["statusCode"])
                print(status)
                exit(8)
        else:
            print ("Found Space : " + self.confluenceSpace + " Name: " + status["name"] )
        self.pageID=self.confluence.get_page_id(self.confluenceSpace, page_name) 
        return self

    def get_page(self):
        page = self.confluence.get_page_by_id(self.pageID+"?expand=body.storage")
        return page
    
    def update_page(self, body, title):
        response = self.confluence.update_page(self.pageID, title, body)
        return response

        










