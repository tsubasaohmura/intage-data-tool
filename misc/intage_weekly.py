import pandas as pd
import paramiko
import re
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog

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

# Functions
def ssh_upload(creds):
    """Upload INTAGE report to MarkLogic server and ingest into database"""
    # Connect to server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**creds)

    # Upload file
    ftp = ssh.open_sftp()
    ftp.put(csv_name, csv_dir + csv_name)
    ftp.close()
    print(f"File has been uploaded to {csv_dir + csv_name}")

    # Ingest data to MarkLogic database
    input("Press Enter to start ingesting the data into MarkLogic database...")
    password = simpledialog.askstring(title="Root password", prompt="Please input root password for sudo command.")
    print(f"You have entered password: {password}")
    while True:
        response = input("""
        *** WARNING! ***
        This will commit data to MarkLogic database.
        Are you completely sure you want to commit the data? [y] """)
        if response.lower() == 'y':
            break
    
    csv_short = csv_name.replace('.csv', '')
    print("\nIngesting data, this might take a while...")
    _in, _out, _err = ssh.exec_command(f"echo {password} | sudo -S \
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

    with open('ml_log.txt', 'w') as f:
        f.write("STDOUT:\n\n")
        f.writelines(_out)
        f.write("\nSTDERR:\n\n")
        f.writelines(_err)
    
    print("Ingestion completed. Check the log in ml_log.txt")


def transformation(file_path, week):
    """Transform INTAGE data according to requirements"""
    # Create a dataframe for each region and combine them at the end
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
    print(f"Modified data has been saved to {csv_name}")


def main():
    # Initialize interface
    print("Initializing...")
    tk.Tk().withdraw()
    
    # Phase 1
    print("\n=== PHASE 1 ===\n\nPlease choose INTAGE raw data .csv file.")
    file_path = filedialog.askopenfilename(initialdir=".", title="Choose weekly report csv file", filetypes=[("CSV File", "*.csv"),])
    if not file_path: 
        sys.exit(0)

    while True:
        print("Please input week date.")
        week = simpledialog.askstring(title="Input week date", prompt="Input week start date in format: YYYY-mm-DD.\nExample: 2020-06-01")
        if not week: 
            sys.exit(0)
        elif re.fullmatch('\d\d\d\d-\d\d-\d\d', week):
            break
        print(f'Unknown format: {week}')
    
    global csv_name
    csv_name = f'{week}_intage_data_weekly.csv'

    while True:
        print("\nYour parameters:")
        print(f"File path:  {file_path}")
        print(f"Week date:  {week}")
        reply = input("\nWould you like to continue with these parameters? [y/n]: ")
        if reply.lower() == 'y':
            print("Starting transformation. This might take some time...")
            transformation(file_path, week)
        elif reply.lower() == 'n':
            print("Aborting operation.")
        else:
            print("Unknown reply. Please enter 'y' or 'n'.")
            continue
        break
    
    # Phase 2
    input("\nPress Enter to begin uploading data to MarkLogic server...")
    print("\n=== PHASE 2 ===\n")
    with open('ml_ssh_creds.txt') as f:
        creds = { line.strip().split('=')[0] : line.strip().split('=')[1] for line in f }

    if not all(creds[key] for key in creds.keys()) or len(creds) != 3:
        raise ValueError("ml_ssh_creds.txt file is not filled correctly. Check information and run the script again.")
    
    print(f"""Credentials for connecting to MarkLogic server:
    IP: {creds['hostname']}
    Username: {creds['username']}
    Password: {creds['password']}
    """)
    input("Press Enter if credentials are correct...")
    print(f"Uploading {csv_name} ...")
    ssh_upload(creds)

    print("\nkthxbye")

if __name__ == "__main__":
    main()