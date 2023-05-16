# OpenCTI Feedly Integration

This Python script allows integration between OpenCTI and Feedly. It fetches indicators of compromise (IoCs) from Feedly and inserts them into OpenCTI.

## Requirements

This script requires Python 3.6 or later. If you do not have Python installed, you can download it from the [official Python website](https://www.python.org/downloads/).

In addition to Python, this script needs several Python packages:

- `pycti==5.7.4`
- `pytz==2023.3`
- `readability-lxml==0.8.1`
- `requests==2.28.2`

## Setup

1. Download or clone this repository to your local machine.

2. Install Python if it's not installed. Check the installation by opening a terminal (Command Prompt for Windows users) and typing `python --version`. You should see a response with the Python version number.

3. Navigate to the directory containing the script using the `cd` command in the terminal. For example: `cd C:\Users\YourName\Downloads\feedly-importer` (Windows) or `cd /home/YourName/Downloads/feedly-importer` (Unix-like systems).

4. Create a Python virtual environment. This step is optional but recommended as it isolates the script and its dependencies from other Python projects on your system. Type the following command in the terminal and press Enter:

```shell
python -m venv env
```

5. Activate the virtual environment. On Windows, type env\Scripts\activate and press Enter. On Unix-like systems, type source env/bin/activate and press Enter. You should see (env) in your terminal prompt.

6. Install the required Python packages. You can do this by running pip install -r requirements.txt.

7. Create a config.ini file in the same directory as the script. This file should contain the following sections and fields:

```ini
[OpenCTI]
url = <Your OpenCTI URL>
api_key = <Your OpenCTI API Key>

[Feedly]
stream_id = <Your Feedly Stream ID>
api_key = <Your Feedly API Key>

[DEFAULT]
fetch_since_midnight = <True or False>
```

Replace the placeholders (<...>) with your actual values.

## Running the Script

You can run the script by using the following command in the terminal:

```shell
python feedly-importer.py
```

## Scheduling the Script

If you want to run this script automatically at regular intervals, you can set up a task scheduler.

### Windows

You can use Task Scheduler:

1. Open Task Scheduler.
2. Create a new task.
3. In the task settings, set the action to start a program.
4. For the program/script, enter the path to your Python executable. For the arguments, enter the path to the script. Both paths should be enclosed in quotes if they contain spaces.

### Unix-like systems (Linux, MacOS)

You can use cron:

1. Open the terminal.
2. Type crontab -e and press Enter.
3. To run the script every 4 hours, add a line like this:

```cron
0 */4 * * * /path/to/python /path/to/feedly-importer.py >> /path/to/log.txt 2>&1
```

Replace /path/to/python with the path to your Python executable, and `/pathto/feedly-importer.py` with the path to the script. This command also redirects the script's output and errors to a log file. Replace `/path/to/log.txt` with the path and filename where you want to store the log file. For instance, you can create a `log.txt` file in the same directory as the script, and set the path to `log.txt`.

Press Ctrl+X to exit the editor, then Y to save the changes and Enter to confirm the file name.

## Troubleshooting

If you experience any issues while setting up or running this script, please ensure that you've followed all the steps in this guide correctly. Most common issues can be resolved by:

- Checking that all the required Python packages are installed. You can check this by running `pip freeze` in the terminal. The output should include all the packages listed in the "Requirements" section above.

- Verifying that your `config.ini` file is correctly formatted and includes all the necessary details.

- Making sure that your Feedly and OpenCTI credentials are correct. You can confirm this by logging into your accounts on the respective platforms. The URL for OpenCTI should not include a forwared slash (/) at the end.

- Ensuring that you're running the script from within the Python virtual environment. If you're not sure, you can activate the environment by following the steps in the "Setup" section above.

If you're still having issues after following these steps, please get in touch for further assistance.

## Contribution

This script is open to improvements and bug fixes. Feel free to fork the repository and make any changes. You can then create a pull request with your proposed changes.