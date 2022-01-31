# Old scripts

This document covers the usage of outdated and miscellaneous scripts that are not used anymore.  
* `intage_auto.py` - PoC (proof of concept) that data extract from INTAGE website can be automated via browser's UI. Decided to go against this fragile approach and do manual extraction weekly. This document won't cover usage of this script.
* `intage_weekly.py` - old console script to transform data and upload it to MarkLogic server. Replaced by GUI version.

# intage_weekly.py

## Requirements

* Python 3.6 >=
* `pandas` module
* `paramiko` module

```python
# Windows
pip install pandas paramiko

# MacOS / Linux
pip3 install pandas paramiko
```

* Fill in `ml_ssh_creds.txt` file with info to access MarkLogic server

```shell
# Example
hostname=10.20.30.40
username=username
password=password
```

## Installation and usage (for Windows)

0. Make sure you've installed correct Python version and `pandas`, `paramiko` modules.
1. Download or clone this repository to a local folder.
2. Download `ALL TSD - All Regions CSV Last Week Auto` report from INTAGE.
3. Open Command Prompt (Win+R -> `cmd`)
4. Go to the local folder where you saved the repository.
5. Run command: `python intage_weekly.py`
6. Follow instructions in Command Prompt window.
