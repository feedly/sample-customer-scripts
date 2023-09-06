# Sample Script: Feedly Article Fetcher (from Boards/Folders)

This Python script fetches articles from Feedly and saves them in various formats (CSV, JSON, SQL). You can configure the script using a config.ini file.

## Requirements

1. Python 3.6 or later.
2. Python libraries: requests, pymysql. You can install them using pip:

```
pip install requests pymysql
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

- The 'token' and 'stream_id' under 'Feedly' section in the config file are required to access the Feedly API. You can generate your Feedly API token from the Manage Team area of your Feedly account.
- The 'columns' option under 'Feedly' allows you to specify the columns you want to save when writing to CSV or MySQL. The column names should match the keys in the JSON objects returned by the Feedly API. If you leave this blank, all columns will be saved.
- The 'output_format' option can be 'csv', 'json', or 'sql'. This controls the format in which the articles are saved.
- The options under the 'MySQL' section are required if you want to save the articles in a MySQL database. You'll need to replace the placeholders with your actual MySQL host, user, password, database, and table names. The user should have read and write permissions on the database.

# Sample Script: Feedly Power Search Exporter

This Python script fetches articles from Feedly using the Power Search API and saves them in a JSON format. Unlike the previous script, this one is more focused on searching for articles based on specific criteria and does not require a config.ini file.

### Requirements

1. Python 3.6 or later.
2. Python library: requests. You can install it using pip:

```
pip install requests
```

3. Obtain your personal Feedly Enterprise Token. For instructions, please visit: [Feedly API Guides](https://feedly.notion.site/Feedly-API-Guides-a8794499f1144f6bb4db4aa363ab5fbd).
4. Create a JSON file containing your search query payload based on Feedly's Power Search documentation.

### Usage

1. Clone this repository.

```
git clone <repository_url>
cd <repository_folder>
```

2. Install the required Python package (if not already installed). It's recommended to use a virtual environment. Here's how to set it up:

```
python3 -m venv venv
source venv/bin/activate
pip install requests
```

3. Run the script:

```
python feedly_power_search.py --token YOUR_FEEDLY_ENTERPRISE_TOKEN --query_file sample_power_search_query.json
```

### Example Usage

To search for articles from the last 7 days using a query stored in `sample_power_search_query.json`:

```
python feedly_power_search.py --token YOUR_FEEDLY_ENTERPRISE_TOKEN --query_file sample_power_search_query.json --days_ago 7
```

To use verbose mode:

```
python feedly_power_search.py --token YOUR_FEEDLY_ENTERPRISE_TOKEN --query_file sample_power_search_query.json -v
```

### Notes

- The `--token` argument is required to access the Feedly API. You can generate your Feedly API token from the Manage Team area of your Feedly account.
- The `--query_file` argument specifies the path to the JSON file containing the search payload.
- The `--output` argument specifies the name of the output file. By default, this is "output.json".
- The `--days_ago` argument allows the user to input the number of days ago articles should be fetched from. This value is converted to milliseconds for the `newerThan` parameter.
- The `-v` or `--verbose` flag enables verbose mode, providing detailed feedback during the continuation loop.
