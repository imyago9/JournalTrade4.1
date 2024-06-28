import pandas as pd
import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'data')

NT_TRADE_DATA_PATH = os.path.join(data_path, 'NinjaTrader', 'trade-performance.csv')
NT_ACCOUNT_SETTINGS_PATH = os.path.join(data_path, 'NinjaTrader', 'account_settings.csv')
NT_SCREENSHOTS_PATH = os.path.join(data_path, 'NinjaTrader', 'screenshots')

TV_ACCOUNT_SETTINGS_PATH = os.path.join(data_path, 'TradingView', 'account_settings.csv')
TV_ACCOUNTS_DATA_PATH = os.path.join(data_path, 'TradingView', 'Accounts')
TV_SCREENSHOTS_PATH = os.path.join(data_path, 'TradingView', 'Accounts', 'screenshots')

print(f"User data directory: {data_path}")
print(f"Ninja Trader Data path: {NT_TRADE_DATA_PATH}")


def update_with_new_ninja_data(file_name):
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

    if os.path.exists(NT_TRADE_DATA_PATH) and os.stat(NT_TRADE_DATA_PATH).st_size > 0:
        existing_trades = pd.read_csv(NT_TRADE_DATA_PATH)

        last_entry_time = existing_trades['EntryT'].max()

        new_trades = new_trades[new_trades['EntryT'] > last_entry_time]

        if not new_trades.empty:
            combined_trades = pd.concat([existing_trades, new_trades], ignore_index=True)
            combined_trades.to_csv(NT_TRADE_DATA_PATH, index=False)

            visibility_df = pd.read_csv(NT_ACCOUNT_SETTINGS_PATH)
            new_accounts = set(combined_trades['Account'].unique()) - set(visibility_df['Account'])
            if new_accounts:
                new_accounts_df = pd.DataFrame(list(new_accounts), columns=['Account'])
                new_accounts_df['Visibility'] = 'visible'
                new_accounts_df['ASize'] = ''  # Add empty ASize column
                visibility_df['BeT'] = ''
                visibility_df = pd.concat([visibility_df, new_accounts_df], ignore_index=True)
                visibility_df.to_csv(NT_ACCOUNT_SETTINGS_PATH, index=False)
                print("account_settings.csv updated with new accounts.")
            else:
                print("No new accounts added to account_settings.csv")
            print("Updated trade-performance with new trades from the broker.")
        else:
            print("No new trades were added. New trades must occur after the last entry time in the existing data.")
    else:
        new_trades.to_csv(NT_TRADE_DATA_PATH, index=False)

        accounts = new_trades['Account'].unique()
        visibility_df = pd.DataFrame(accounts, columns=['Account'])
        visibility_df['Visibility'] = 'visible'
        visibility_df['ASize'] = ''
        visibility_df['BeT'] = ''
        visibility_df.to_csv(NT_ACCOUNT_SETTINGS_PATH, index=False)
        print("account_settings.csv created for the firt time..")
        print("trade-performance created for the firt time..")


def update_with_tradingview_data(file_name, account_name):
    account_file_path = os.path.join(TV_ACCOUNTS_DATA_PATH, f'{account_name}.csv')
    if not os.path.exists(file_name) or os.stat(file_name).st_size == 0:
        print("Missing or empty TradingView data. Please import data as instructed and try again.")
        return

    tradingview_df = pd.read_csv(file_name)

    # Separate trade rows and commission rows
    trade_rows = tradingview_df[~tradingview_df['Action'].str.contains('Commission')]
    commission_rows = tradingview_df[tradingview_df['Action'].str.contains('Commission')]
    account_total_commission = commission_rows['P&L'].sum()

    def parse_action_precise(action):
        instrument_match = re.search(r'for symbol (.+?) ', action)
        qty_match = re.search(r'(\d+) shares', action)
        exit_price_match = re.search(r'at price ([\d.]+)', action)
        entry_price_match = re.search(r'Position AVG Price was ([\d.]+)', action)

        if "Close short" in action:
            market_pos = "Short"
        elif "Close long" in action:
            market_pos = "Long"
        else:
            market_pos = None

        instrument = instrument_match.group(1) if instrument_match else None
        qty = int(qty_match.group(1)) if qty_match else None
        entry_price = float(entry_price_match.group(1)) if entry_price_match else None
        exit_price = float(exit_price_match.group(1)) if exit_price_match else None

        return instrument, market_pos, qty, entry_price, exit_price

    parsed_trades_precise = []
    for index, row in trade_rows.iterrows():
        instrument, market_pos, qty, entry_price, exit_price = parse_action_precise(row['Action'])
        time_column = row['Time']
        profit = row['P&L']


        parsed_trades_precise.append([instrument, market_pos, qty, entry_price, exit_price, time_column, profit])

    parsed_trades_df_precise = pd.DataFrame(parsed_trades_precise, columns=[
        'Instrument', 'LorS', 'Qty', 'EntryP', 'ExitP', 'Time', 'Profit'
    ])

    if os.path.exists(account_file_path) and os.stat(account_file_path).st_size > 0:
        existing_trades = pd.read_csv(account_file_path)
        last_time_column = existing_trades['Time'].max()

        new_trades = parsed_trades_df_precise[parsed_trades_df_precise['Time'] > last_time_column]

        if not new_trades.empty:
            combined_trades = pd.concat([existing_trades, new_trades], ignore_index=True)
            combined_trades.to_csv(account_file_path, index=False)
            print(f"Updated {account_name}.csv with new trades from the TradingView data.")
        else:
            print("No new trades were added. New trades must occur after the last exit time in the existing data.")
    else:
        reply, new_account_name = FramelessMessageBox.show_message(
            'The csv uploaded does not match any account, do you wish to save it as a new account?', True
        )
        if reply and new_account_name.strip():
            new_account_file_path = os.path.join(TV_ACCOUNTS_DATA_PATH, f'{new_account_name}.csv')
            parsed_trades_df_precise.to_csv(new_account_file_path, index=False)
            print(f"Created {new_account_name}.csv for the first time with TradingView data.")

            if os.path.exists(TV_ACCOUNT_SETTINGS_PATH):
                visibility_df = pd.read_csv(TV_ACCOUNT_SETTINGS_PATH)
                if new_account_name not in visibility_df['Account'].values:
                    new_account_df = pd.DataFrame([[new_account_name, 'visible', '', '', round(float(account_total_commission), 2)]],
                                                  columns=['Account', 'Visibility', 'ASize', 'BeT', 'Commission'])
                    visibility_df = pd.concat([visibility_df, new_account_df], ignore_index=True)
                    visibility_df.to_csv(TV_ACCOUNT_SETTINGS_PATH, index=False)
                    print("Updated account_settings.csv with new account.")
                else:
                    print("Account already exists in account_settings.csv.")
            else:
                new_account_df = pd.DataFrame([[new_account_name, 'visible', '', '', round(float(account_total_commission), 2)]],
                                              columns=['Account', 'Visibility', 'ASize', 'BeT', 'Commission'])
                new_account_df.to_csv(TV_ACCOUNT_SETTINGS_PATH, index=False)
                print("Created account_settings.csv for the first time with new account.")
        elif not new_account_name.strip():
            print("Account name cannot be empty. The file was not saved.")


class FramelessMessageBox(QDialog):
    def __init__(self, message, with_input=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self.initUI(message, with_input)
        self.oldPos = None

    def initUI(self, message, with_input):
        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.text_input = None
        if with_input:
            self.text_input = QLineEdit(self)
            layout.addWidget(self.text_input)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        if event.buttons() == QtCore.Qt.LeftButton:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()


    @staticmethod
    def show_message(message, with_input=False, parent=None):
        dialog = FramelessMessageBox(message, with_input, parent)
        result = dialog.exec_()
        if with_input:
            return result == QDialog.Accepted, dialog.text_input.text() if dialog.text_input else ''
        return result == QDialog.Accepted, ''
