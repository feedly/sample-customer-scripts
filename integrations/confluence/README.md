# Daily_feedly_board

## What does the program do?

The daily_feedly_board program is a quick, simple, and beautiful integration to quickly bring news from the board to a Confluence page.

## Getting started

To use the script, you need to download several Python libraries (all listed in requirements.txt).

# Add your configs

Create two config JSON files, one for your Feedly credentials and one for your Confluence credentials. 
The configs should look like this:

config.json (for Feedly)
```json
{
    "apiToken" : "Insert the API Token here" 
}

confluence_config.json
```json
{
    "confluence":"https://your-confluence-URL.com"
    ,"user":"Email"
    ,"password": "Confluence API Token"
    ,"space": "Confluence Space (Key of the Space)"
}
```

# Last steps 

Now you need to go to the main.py file to edit lines 9 and 10.

Line 10 (page_name): As the variable name suggests, you enter the title of the Confluence page you want to edit here. (IMPORTANT: This page must exist in the area defined in the config.)
Line 11 (board_streamID): Enter the streamID of the Feedly board here. You can find this streamID under the settings of the specific board, under share at the very bottom.


The last and most important step is to place a placeholder on the Confluence page where the script should place the articles at the end.

This placeholder looks like this:
<div class=Feedly_placeholder></div>

Important: This div should be inside an HTML macro.

# Run the Script
Now you can start the script. Have fun! :)

# Nice to know

If you want to visually customize the articles in Confluence, you can look into the HTMLTemplate folder. There, you will find the current HTML template that you can customize. In the end, you need to adjust the HTML code in the main.py file to make these changes permanent and applied.