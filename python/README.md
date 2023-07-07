# Feedly API Article Fetcher

This Python script fetches articles from Feedly and saves them in various formats (CSV, JSON, SQL). You can configure the script using a config.ini file.

## Requirements

1. Python 3.6 or later.
2. Python libraries: requests, csv, json, pymysql, configparser. You can install them using pip:

```
pip install requests csv json pymysql configparser
```

3. Obtain your personal Feedly API token. For instructions, please visit: [Feedly API Guides](https://feedly.notion.site/Feedly-API-Guides-a8794499f1144f6bb4db4aa363ab5fbd).
4. Find the unique identifier for the Feedly stream (stream_id) you want to fetch articles from.

## Usage

1. Clone this repository.

```
git clone <repository_url>
cd <repository_folder>
```

2. Install the required Python packages (if not already installed). It's recommended to use a virtual environment. Here's how to set it up:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set up your MySQL server (if you're planning to save to MySQL).

On Ubuntu, you can do this using the following commands:

```
sudo apt-get update
sudo apt-get install mysql-server
sudo mysql_secure_installation
```

On Mac OS, you can use Homebrew:

```
brew update
brew install mysql
mysql.server start
mysql_secure_installation
```

4. Create your MySQL database and user (if necessary) and grant necessary permissions for the user on the database.
5. Create a config.ini file in the same directory as your script. A example config file is included in this repo. Replace any placeholders with your actual data.
6. Run the script:

```
python feedly_fetcher.py
```

7. The articles will be fetched and saved in the format specified in your config file.

## Notes

- The 'token' and 'stream_id' under 'Feedly' section in the config file are required to access the Feedly API. You can generate your Feedly API token from the Manage Team area of your Feedly account. Here are more detailed instructions: https://feedly.notion.site/How-to-create-and-manage-your-Feedly-API-access-tokens-a5b6cd75aaff4144beebecc56dcb06cc.
- The 'columns' option under 'Feedly' allows you to specify the columns you want to save when writing to CSV or MySQL. The column names should match the keys in the JSON objects returned by the Feedly API. If you leave this blank, all columns will be saved.
- The 'output_format' option can be 'csv', 'json', or 'sql'. This controls the format in which the articles are saved.
- The options under the 'MySQL' section are required if you want to save the articles in a MySQL database. You'll need to replace the placeholders with your actual MySQL host, user, password, database, and table names. The user should have read and write permissions on the database.