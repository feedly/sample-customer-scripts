# OpenCTI x Feedly Integration

This Python script provides a sample integration between OpenCTI and Feedly. It fetches STIX objects from Feedly and inserts them into your OpenCTI server. This script was tested on MacOS Ventura 13.4 with Python 3.11.3. The OpenCTI environment used for testing had both the MITRE and OpenCTI dataset connectors enabled.

## Instructions

1. Download or clone this repository to your local machine.

2. Install Python if it's not installed. Check the installation by opening a terminal (Command Prompt for Windows users) and typing `python3 --version`. You should see a response with the Python version number.

3. Install the prerequisites, including readability-lxml dependencies and libmagic (see below for detailed steps).

4. Navigate to the directory containing the script using the `cd` command in the terminal. For example: `cd C:\Users\[YourName]\Downloads\feedly-importer` (Windows) or `cd /home/[YourName]/Downloads/feedly-importer` (Unix-like systems).

5. Create a Python virtual environment. This step is optional but recommended as it isolates the script and its dependencies from other Python projects on your system. If you have trouble installing the required Python packages, make sure you use Python 3.11 (or higher). This version of Python might help avoid issues when instaling the readability-lxml and its dependencies. Type the following command in the terminal and press Enter:

```shell
python3 -m venv venv
```

6. Activate the virtual environment. On Windows, type `venv\Scripts\activate` and press Enter. On Unix-like systems, type `source venv/bin/activate` and press Enter. You should see (venv) in your terminal prompt.

7. Install the required Python packages. You can do this by running `pip3 install -r requirements.txt`.

8. Create a config.ini file in the same directory as the script. This file should contain the following sections and fields:

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

Replace the placeholders (<...>) with your actual values. Do not include quotations (`"`)around your values. The OpenCTI URL should be formatted without anything after the hostname (e.g., https://10.0.0.1).

## Requirements

This script was tested on Python 3.11 on MacOS. If you do not have Python installed, you can download it from the [official Python website](https://www.python.org/downloads/).

### Installing readability-lxml Dependencies

The readability-lxml package has additional dependencies that need to be installed depending on your operating system.

**MacOS**

In MacOS, you can use the package manager Homebrew to install the dependencies. If you don't have Homebrew installed, you can install it with the following command in your terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After you install Homebrew, it will ask you to add it to your PATH. Please follow the instructions on how do do this. Once you install Homebrew, you may need to open a new terminal window for the brew commands to work.

On MacOS, you need to install libxml2 and libxslt. You can do this using Homebrew:

```shell
brew install libxml2 libxslt
```

**Linux**

For Ubuntu and other Debian-based distributions, you can use the following commands:

```shell
sudo apt-get update
sudo apt-get install libxml2-dev libxslt-dev
```

**Windows**

For Windows, the easiest way to install the dependencies is to use a precompiled binary wheel for lxml, which includes the required libxml2 and libxslt libraries. You can install it with pip:

```bash
pip3 install lxml
```

### Installing libmagic

The Python package magic used in this script requires the libmagic library. This is a system-level library that needs to be installed separately.

Here are instructions for installing libmagic on various operating systems:

**macOS**

If you're using macOS, you can use Homebrew to install the library:

```shell
brew install libmagic
```

**Linux**

If you're using a Debian-based Linux distribution (like Ubuntu), you can use apt-get to install the library:

```shell
sudo apt-get install libmagic1
```

If you're using a Red Hat-based Linux distribution (like CentOS), you can use yum to install the library:

```shell
sudo yum install file-libs
```

**Windows**

On Windows, the situation is a bit more complex because libmagic isn't readily available. However, the python-magic-bin package provides pre-compiled binary wheels for the magic module, which include the necessary library:

```shell
pip install python-magic-bin==0.4.14
```

Please note, these instructions are for the command line (Terminal for macOS and Linux, Command Prompt for Windows). If you're not familiar with using the command line, you may need to learn how to navigate it or seek further assistance.

## Running the Script

You can run the script by using the following command in the terminal:

```shell
python3 feedly-importer.py
```

## Scheduling the Script

If you want to run this script automatically at regular intervals, you can set up a task scheduler.

### Unix-like systems (Linux, MacOS)

You can use cron:

1. Open the terminal.
2. Type `crontab -e` and press Enter.
3. To run the script every 4 hours, add a line like this:

```cron
0 */4 * * * /path/to/python /path/to/feedly-importer.py >> /path/to/log.txt 2>&1
```

Replace /path/to/python with the path to your Python executable, and `/pathto/feedly-importer.py` with the path to the script. This command also redirects the script's output and errors to a log file. Replace `/path/to/log.txt` with the path and filename where you want to store the log file. For instance, you can create a `log.txt` file in the same directory as the script, and set the path to `log.txt`.

Press Ctrl+X to exit the editor, then Y to save the changes and Enter to confirm the file name.

### Windows

You can use Task Scheduler:

1. Open Task Scheduler.
2. Create a new task.
3. In the task settings, set the action to start a program.
4. For the program/script, enter the path to your Python executable. For the arguments, enter the path to the script. Both paths should be enclosed in quotes if they contain spaces.

## Troubleshooting

If you experience any issues while setting up or running this script, please ensure that you've followed all the steps in this guide correctly. Most common issues can be resolved by:

- Checking that all the required Python packages are installed. You can check this by running `pip3 freeze` in the terminal. The output should include all the packages listed in the "Requirements" section above.

- Verifying that your `config.ini` file is correctly formatted and includes all the necessary details *(Important: The URL for OpenCTI should not include a forward slash (/) at the end - or anything after the hostname).*

- Making sure that your Feedly and OpenCTI credentials are correct. You can confirm this by logging into your accounts on the respective platforms. The account used to access OpenCTI should have administrative privileges.

- Ensuring that you're running the script from within the Python virtual environment. If you're not sure, you can activate the environment by following the steps in the "Setup" section above.

- In case of network connectivity issues, the script may terminate abruptly. Re-running the script may help after waiting a few minutes.

- Doublecheck that your OpenCTI instances is accessible and is able to be pinged from the client used to run this script.

If you're still having issues after following these steps, please get in touch for further assistance.

## Contribution

This script is open to improvements and bug fixes. Feel free to fork the repository and make any changes. You can then create a pull request with your proposed changes.
