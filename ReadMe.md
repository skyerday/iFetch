# iFetch

A robust Python utility for efficiently downloading files and folders from iCloud Drive, designed for bulk data recovery and migration. This tool helps users easily retrieve their data from iCloud Drive when Apple's native solutions are insufficient.

## Features

- 🔐 Secure authentication with 2FA/2SA support
- 📁 Recursive directory downloading
- ⏸️ Resume-capable downloads
- 📊 Progress tracking with detailed statistics
- 🔍 Directory listing functionality
- ⚡ Efficient file handling with streaming downloads
- 🔄 Skip existing files to avoid duplicates

## Why This Tool?

While iCloud Drive provides excellent cloud storage integration, downloading large amounts of data or entire directories can be challenging through the standard interfaces. This tool addresses common scenarios such as:

- Recovering data after disabling iCloud Drive
- Migrating data between accounts
- Creating local backups
- Bulk downloading specific directories

## Installation

1. Create and activate a virtual environment:
```sh
python3 -m venv ivenv
source venv/bin/activate
```

2. Install Python dependencies:
```sh
pip install pyicloud tqdm keyring
```

3. Install system keyring dependencies:
For Ubuntu/Debian:
```sh
sudo apt-get install python3-keyring
```

For macOS:
```sh
brew install python-keyring
```

4. Configuration
Store your iCloud credentials securely:
```sh
icloud --username=your@email.com
```
The tool will prompt for your password and store it securely in your system's keyring.


## Usage
### List Directory Contents
View the contents of an iCloud Drive directory:
```sh
python main.py Documents --list
```

### Download Files/Folders
Download a specific directory or file:
```sh
python main.py Documents/Photos -o ~/Downloads/icloud-photos
python main.py Documents/Programming ~/LocalDoc/Programming
```


## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
pyicloud for the excellent iCloud API wrapper
tqdm for the progress bar functionality

## Troubleshooting

### Authentication Issues
* Ensure your Apple ID and password are correct
* For 2FA, make sure you have access to your trusted devices


### Download Problems
* Check your internet connection
* Verify you have sufficient local storage
* Ensure your iCloud Drive is properly synced
