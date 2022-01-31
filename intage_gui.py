import os
import pandas as pd
import paramiko
from paramiko import AuthenticationException
import PySimpleGUI as sg
import re
import sys

# -- Mappings and variables

# Column region-index mapping
COLUMNS = {
    "Common": range(0, 9),
    "Total": range(9, 14),
    "Hokkaido": range(14, 19),
    "Michinoku": range(19, 24),
    "Hokuriku": range(24, 29),
    "East Japan": range(29, 34),
    "Kanto": range(34, 39),
    "Tokyo": range(39, 44),
    "Central Japan": range(44, 49),
    "Kinki Shikoku": range(49, 54),
    "West Japan": range(54, 59),
    "Okinawa": range(59,64),
}

# Final header
RAW_HEADER = ["Channel", "Category", "Maker", "Product_JP", "Package_Size", 
    "Region", "Kubun", "Package_Size_Check", "Intage_Dates", "Values_Liters", 
    "Values_Unit_Case", "Values_JPY", "Values_Turn", "Values_Coverage"]

FINAL_HEADER = ["Channel", "Category", "Maker", "Product_JP", "Product_EN",
    "Package_Family", "Package_Size", "Brand", "JanCode", "Region",
    "Kubun", "Package_Size_Check", "Intage_Dates", "Dates", "Values_Liters",
    "Values_Unit_Case", "Values_JPY", "Values_Turn", "Values_Coverage"]

# Package mapping
PACKAGES = {
    "TTL": "TOTAL",
    "PET 1-350ml": "PET",
    "PET 351-650ml": "PET",
    "PET 651-1250ml": "PET",
    "PET 1451-2000ml": "PET",
    "PET Others": "PET",
    "Can 1-200ml": "CAN",
    "Can 201-300ml": "CAN",
    "Can 301-350ml": "CAN",
    "Can 351-500ml": "CAN",
    "Bottle Can 1-350ml": "BOTTLE CAN",
    "Bottle Can 351-650ml": "BOTTLE CAN",
    "Bottle Can Others": "BOTTLE CAN",
    "Paper Pack 1-350ml": "PAPER PACK",
    "Paper Pack 651-1000ml": "PAPER PACK",
    "Paper Pack 351-650ml": "PAPER PACK",
    "Bottle": "BOTTLE",
    "Cup": "CUP",
    "Others": "OTHERS",
}

# Variables
csv_name = ""
csv_dir = "/home/mladmin/csv/MI/"
menu = ["filename", "-BROWSE-", "week", "hostname", "username", "password", "-START-"]
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Special function for .exe building
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# -- GUI Setup

# Set GUI to Coca-Cola theme
sg.theme_add_new("Coca-Cola", {
        'BACKGROUND': '#f40008', # Coca-Cola Red color
        'TEXT': 'white',
        'INPUT': '#dedede',
        'SCROLL': '#dedede',
        'TEXT_INPUT': 'black',
        'BUTTON': ('black', 'white'),
        'PROGRESS': sg.DEFAULT_PROGRESS_BAR_COLOR,
        'BORDER': 1,
        'SLIDER_DEPTH': 0,
        'PROGRESS_DEPTH': 0}
        )

sg.theme("Coca-Cola")

# Layout and window setup
layout = [
    [
        sg.Output(size=(70, 20), key='-OUT-'),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Image(filename=resource_path("icon.png"))],
            [
                sg.Column([
                    [sg.Text("Filename")],
                    [sg.Text("Week (YYYY-mm-DD)")],
                    [sg.Text("MarkLogic Hostname")],
                    [sg.Text("MarkLogic Username")],
                    [sg.Text("MarkLogic Password")],
                ]), 
                sg.Column([
                    [
                        sg.Input(size=(16,1), enable_events=True, key="filename", disabled_readonly_background_color="gray"), 
                        sg.FileBrowse(target="filename", file_types=[("CSV File", "*.csv"),], initial_folder=".", key="-BROWSE-")
                    ],
                    [sg.Input(size=(16,1), enable_events=True, key="week", disabled_readonly_background_color="gray")],
                    [sg.Input(default_text="10.212.47.69", size=(16,1), enable_events=True, key="hostname", disabled_readonly_background_color="gray")],
                    [sg.Input(default_text="mladmin", size=(16,1), enable_events=True, key="username", disabled_readonly_background_color="gray")],
                    [sg.Input(size=(16,1), enable_events=True, key="password", password_char="*", disabled_readonly_background_color="gray")],
                ])
            ],
            [sg.Text()], # Empty line
            [sg.Button("Start", font=("Helvetica",24), size=(10,0), key="-START-")]
        ], element_justification="center"), 
    ]
]

window = sg.Window("INTAGE Data Tool", layout=layout)


# -- Helper functions

def disable(menu):
    """Disables elements in 'menu'."""
    for key in menu: window[key].update(disabled=True)


def enable(menu):
    """Enables elements in 'menu'."""
    for key in menu: window[key].update(disabled=False)


def printr(text):
    """Custom print function to refresh window after every print."""
    print(text)
    window.refresh()


# -- Main processing functions

def safety_check(values):
    """Check if provided credentials are correct before starting the job."""
    try:
        # Values check
        printr("Checking input values...")
        assert os.path.exists(values['filename'])
        assert re.fullmatch('\d\d\d\d-\d\d-\d\d', values['week'])
        assert re.fullmatch('\d+\.\d+\.\d+\.\d+', values['hostname'])
        assert values['username']
        assert values['password']
        printr("Values check passed.")
        # Connection check
        printr("Testing connection...")
        ssh.connect(hostname=values['hostname'], username=values['username'], password=values['password'])
        assert ssh.get_transport()
        ssh.close()
        printr("Test connection successful.")
    except AssertionError:
        raise AssertionError("Values check failed. Please check your input values and try again.")
    except AuthenticationException:
        raise AuthenticationException("Test authentication to MarkLogic server failed.\nPlease check your credentials and try again.")
    except TimeoutError:
        raise TimeoutError("Test connection to MarkLogic server timed out. Are you connected to proxy?\nPlease check proxy, hostname and try again.")
    except Exception as e:
        raise Exception("Unknown exception!\n" + repr(e))

def ssh_upload(values):
    """Upload INTAGE report to MarkLogic server and ingest into database"""
    # Connect to server
    ssh.connect(hostname=values['hostname'], username=values['username'], password=values['password'])

    # Upload file
    printr(f"Uploading {csv_name} to MarkLogic database...")
    ftp = ssh.open_sftp()
    ftp.put(csv_name, csv_dir + csv_name)
    ftp.close()
    printr(f"File has been uploaded to {csv_dir + csv_name}")

    # Ingest data to MarkLogic database
    csv_short = csv_name.replace('.csv', '')
    printr("\nIngesting data into database, this might take a while...")
    _in, _out, _err = ssh.exec_command(f"echo {values['password']} | sudo -S \
/opt/MarkLogic/mlcp/bin/mlcp.sh import \
-ssl \
-host 10.212.47.72 \
-port 8000 \
-database MarketingIntelligence_POC \
-mode local \
-username admin-user \
-password admin \
-input_file_path {csv_dir + csv_name} \
-input_file_type delimited_text \
-delimiter \",\" \
-delimited_root_name TSD \
-generate_uri true \
-output_uri_replace \"{csv_dir + csv_name}, '/{csv_short}'\" \
-output_uri_prefix \"/MI/{csv_short}\" \
-output_uri_suffix \".xml\" \
-output_collections \"TSD,{csv_short}\" \
-output_permissions \"read-role,read\" \
-thread_count 48")

    printr(f"\n--- STDOUT response:")
    for line in _out: printr(line)
    printr(f"\n--- STDERR response:")
    for line in _err: printr(line)
    ssh.close()
    printr("\nIngestion completed.")


def transformation(file_path, week):
    """Transform INTAGE data according to requirements"""
    # Create a dataframe for each region and combine them at the end
    printr(f"Transforming file: {file_path}\nThis might take a while...")
    dataframes = []
    regions = list(COLUMNS.keys())[2:] # list of 10 regions derived from keys
    for region in regions:
        df = pd.read_csv(file_path, header=None, names=RAW_HEADER, 
                        encoding='cp932', skiprows=[0, 1], usecols=[*COLUMNS['Common'], *COLUMNS[region]])
        df['Region'] = region
        dataframes.append(df)

    df_all = pd.concat(dataframes, ignore_index=True)

    # Transform the dataframe according to requirements
    df_all = df_all.reindex(columns=FINAL_HEADER)
    df_all['Package_Family'] = df_all.apply(lambda row: PACKAGES[row['Package_Size']], axis=1)
    df_all['Dates'] = week
    df_all['Intage_Dates'] = week[-4:].replace('-', '.') + '-'

    # Final output
    df_all.to_csv(csv_name, encoding='utf-8', index=False, quoting=0)
    printr(f"Modified data has been saved to {csv_name}")


def main():
    # Introductory message
    window.finalize()
    window['-OUT-'].update("Welcome to INTAGE Data Tool!\nCheck parameters on the right and press \"Start\" to begin.\n\n")

    # Event loop
    while True:
        enable(menu)
        event, values = window.read()
        #print(event, values)  # Use for debugging only
        if event in (sg.WINDOW_CLOSED,):
            window.close()
            sys.exit(0)
        if event in ("-START-"):
            disable(menu)
            try:
                # Validate input and connection
                safety_check(values)

                # Transform data
                printr("\n=== Data Transformation ===\n")
                global csv_name
                csv_name = f"{values['week']}_intage_data_weekly.csv"
                transformation(values['filename'], values['week'])
                
                # Upload to MarkLogic
                printr("\n=== Upload to MarkLogic ===\n")
                ssh_upload(values)

                printr("\nAll done! Check server output above in case there were any errors.")
            except Exception as e:
                sg.popup("Something went wrong! Error:\n", str(e) + "\n", title="Error", background_color="lightgray", text_color="black")
                printr("Error occured. Please fix the problem and try again.\n")

main()