# INTAGE Data Tool

Tool for automating weekly data upload from INTAGE I-Canvas interface to CCBJI MarkLogic database.  

Weekly data upload consists of 3 stages:
1. Downloading weekly report from INTAGE using **I-Canvas** web interface.
2. Prepare and transform data to necessary format.
3. Upload transformed data to MarkLogic server (FTP) and ingest into the database (SSH).

This tool automates steps #2 and #3.  
Step #1 is done manually.

## Download
Please see [Releases](/releases) tab for `intage_gui.exe` file and download it.

## Usage
* Download `ALL TSD - All Regions CSV Last Week Auto` report from INTAGE for the last week.
* Run previously downloaded `intage_gui.exe`.
    * ❗ **NOTE**: when running the file for the first time, Windows might prevent it from running. In this case, click "More info" -> "Run anyway".
* In app window, select downloaded report, fill in week number and password to MarkLogic database.
* Click `Start` and wait util the upload process finishes.
    * ❗ **NOTE**: app might freeze and show "Not responding" status during upload process. This is normal, please wait until it finishes.

# How to build executable file
Information below is for app maintainers only. Feel free to skip if you're just using the executable file.

❗ **NOTE 1**: You can build .exe files only on Windows.

❗ **NOTE 2**: PyInstaller currently officially doesn't support Python 3.8 =>. Please install Python 3.6 or Python 3.7 on your system.

## Install necessary packages
Below we will assume that you are using Python 3.6 or 3.7 as your main interpreter on the system.
```shell
pip install pandas paramiko PySimpleGUI pywin32 pyinstaller auto-py-to-exe
```

We will be using `auto-py-to-exe`, which is a GUI wrapper around `pyinstaller` module.

## Building executable
1. Open command prompt, go to the script directory and run `auto-py-to-exe` command. This will bring up a GUI interface.
2. Setup build configuration:
    * Browse to `intage_gui.py` script location
    * Choose `One File`
    * Choose `Window Based (hide the console)`
    * Under `Additional Files`, click `Add Files` and choose `icon.png` in the same folder
3. Confirm and press `CONVERT .PY TO .EXE`. Your executable will be put into `output` folder.
4. Check that your executable works.