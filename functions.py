import pandas as pd
import os
import sys
from appdirs import AppDirs

APP_NAME = 'JournalTrade'
APP_AUTHOR = 'Y'

dirs = AppDirs(APP_NAME, APP_AUTHOR)
user_data_dir = dirs.user_data_dir

if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

data_path = os.path.join(user_data_dir, 'data')
if not os.path.exists(data_path):
    os.makedirs(data_path)

screenshots_path = os.path.join(data_path, 'screenshots')
if not os.path.exists(screenshots_path):
    os.makedirs(screenshots_path)

use_data_path = os.path.join(data_path, 'to_use_data.csv')
visibility_file_path = os.path.join(data_path, 'account_settings.csv')

print(f"User data directory: {user_data_dir}")
print(f"Data path: {use_data_path}")


def update_with_new_data(file_name):
    if not os.path.exists(file_name) or os.stat(file_name).st_size == 0:
        print("Missing or empty data from broker. Please import data as instructed and try again.")
        return

    new_trades = pd.read_csv(file_name)

    # List of required columns and their mappings
    required_columns = {
        'Instrument': 'Instrument',
        'Account': 'Account',
        'Market pos.': 'LorS',
        'Qty': 'Qty',
        'Entry price': 'EntryP',
        'Exit price': 'ExitP',
        'Entry time': 'EntryT',
        'Exit time': 'ExitT',
        'Profit': 'Profit',
        'Commission': 'Com'
    }

    # Check for missing columns
    missing_columns = set(required_columns.keys()) - set(new_trades.columns)
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return

    new_trades.rename(columns=required_columns, inplace=True)
    new_trades = new_trades[list(required_columns.values())]

    columns_to_modify = ['Profit', 'Com']
    for column in columns_to_modify:
        new_trades[column] = new_trades[column].astype(str).str.replace(r'[$,)]', '', regex=True).str.replace(r'\(',
                                                                                                              '-',
                                                                                                              regex=True)
        new_trades[column] = new_trades[column].astype(float).round(2)
    for column in ['EntryT', 'ExitT']:
        new_trades[column] = pd.to_datetime(new_trades[column], errors='coerce')

    if os.path.exists(use_data_path) and os.stat(use_data_path).st_size > 0:
        existing_trades = pd.read_csv(use_data_path)

        last_entry_time = existing_trades['EntryT'].max()

        new_trades = new_trades[new_trades['EntryT'] > last_entry_time]

        if not new_trades.empty:
            combined_trades = pd.concat([existing_trades, new_trades], ignore_index=True)
            combined_trades.to_csv(use_data_path, index=False)

            visibility_df = pd.read_csv(visibility_file_path)
            new_accounts = set(combined_trades['Account'].unique()) - set(visibility_df['Account'])
            if new_accounts:
                new_accounts_df = pd.DataFrame(list(new_accounts), columns=['Account'])
                new_accounts_df['Visibility'] = 'visible'
                new_accounts_df['ASize'] = ''  # Add empty ASize column
                visibility_df['TargetLines'] = 'Off'  # Add empty ASize column
                visibility_df['BeT'] = ''
                visibility_df = pd.concat([visibility_df, new_accounts_df], ignore_index=True)
                visibility_df.to_csv(visibility_file_path, index=False)
                print("account_settings.csv updated with new accounts.")
            else:
                print("No new accounts added to account_settings.csv")
            print("Updated to_use_data with new trades from the broker.")
        else:
            print("No new trades were added. New trades must occur after the last entry time in the existing data.")
    else:
        new_trades.to_csv(use_data_path, index=False)

        accounts = new_trades['Account'].unique()
        visibility_df = pd.DataFrame(accounts, columns=['Account'])
        visibility_df['Visibility'] = 'visible'
        visibility_df['ASize'] = ''
        visibility_df['TargetLines'] = 'Off'
        visibility_df['BeT'] = ''
        visibility_df['LastUpdatedProfit'] = ''
        visibility_df.to_csv(visibility_file_path, index=False)
        print("account_settings.csv created for the firt time..")
        print("to_use_data created for the firt time..")
