from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
import os
from functions import NT_ACCOUNT_SETTINGS_PATH, TV_ACCOUNT_SETTINGS_PATH, TV_ACCOUNTS_DATA_PATH, update_with_new_ninja_data, update_with_tradingview_data
import pandas as pd


class ManageDataWidget(QtWidgets.QDialog):
    csv_uploaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Account Data")
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.15), int(screen_height * 0.15))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.initUI()

    def initUI(self):
        self.manageDataLayout = QVBoxLayout(self)

        self.manageDataLayoutTop = QVBoxLayout()
        self.manageDataLayoutBottom = QVBoxLayout()

        self.setupTopbar()
        self.check_and_add_account_buttons()

        self.close_button = QtWidgets.QPushButton("Close", clicked=self.close)
        self.manageDataLayoutBottom.addWidget(self.close_button)

        # Add top and bottom layouts to the main layout
        self.manageDataLayout.addLayout(self.manageDataLayoutTop)
        self.manageDataLayout.addLayout(self.manageDataLayoutBottom)

        self.setLayout(self.manageDataLayout)  # Set the main layout for the dialog

        self.oldPos = None

    def setupTopbar(self):
        def acc_button():
            self.add_account_button()

        self.manageDataLayout_horizontal_topbar = QHBoxLayout()
        self.account_type_combobox = QComboBox(self)
        self.account_type_combobox.addItem("NinjaTrader Account(s)")
        self.account_type_combobox.addItem("TradingView Account(s)")
        self.account_type_combobox.setCurrentIndex(-1)  # Set to the blank item

        self.account_settings_button = QPushButton('+', clicked=acc_button)
        self.account_delete_button = QPushButton('-', clicked=self.prompt_account_deletion)
        self.manageDataLayout_horizontal_topbar.addWidget(self.account_type_combobox)
        self.manageDataLayout_horizontal_topbar.addWidget(self.account_settings_button)
        self.manageDataLayout_horizontal_topbar.addWidget(self.account_delete_button)
        self.manageDataLayoutTop.addLayout(self.manageDataLayout_horizontal_topbar)

    def prompt_account_deletion(self):
        reply = QMessageBox.question(None,'Remove accounts.',f'Are you sure you want to delete the {self.account_type_combobox.currentText()}?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print('Deleting accounts.')
        else:
            print('Accounts were not deleted.')

    def check_and_add_account_buttons(self):
        self.data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'data')
        print(f"Checking directories in: {self.data_dir}")
        self.ninja_dir = os.path.join(self.data_dir, 'NinjaTrader')
        self.tradingview_dir = os.path.join(self.data_dir, 'TradingView')
        self.tradingview_accounts_dir = TV_ACCOUNTS_DATA_PATH

        if os.path.exists(self.ninja_dir):
            print("NinjaTrader directory exists")
            ninja_button = QPushButton('NinjaTrader Account(s)', clicked=self.open_ninja_trader_accounts)
            self.manageDataLayoutTop.addWidget(ninja_button)
        else:
            print("NinjaTrader directory does not exist")

        if os.path.exists(self.tradingview_dir):
            print("TradingView directory exists")
            tradingview_button = QPushButton('TradingView Account(s)', clicked=self.open_tradingview_accounts)
            self.manageDataLayoutTop.addWidget(tradingview_button)
        else:
            print("TradingView directory does not exist")

    def add_account_button(self):
        selected_account_type = self.account_type_combobox.currentText()
        def a():
            print('a')

        def selected_account_path():
            if selected_account_type == 'NinjaTrader Account(s)':
                self.account_button = QPushButton(selected_account_type, clicked=self.open_ninja_trader_accounts)
                return self.ninja_dir
            elif selected_account_type == 'TradingView Account(s)':
                self.account_button = QPushButton(selected_account_type, clicked=self.open_tradingview_accounts)
                return self.tradingview_dir

        if selected_account_type:
            account_path = selected_account_path()
            if os.path.exists(account_path):
                print(f'{selected_account_type} folder already exists, can\'t be added')
            else:
                self.manageDataLayoutTop.addWidget(self.account_button)
                os.makedirs(account_path, exist_ok=True)
                if selected_account_type == 'TradingView Account(s)':
                    os.makedirs(TV_ACCOUNTS_DATA_PATH, exist_ok=True)
                print(f'{selected_account_type} folder created and button added')

    def open_tradingview_accounts(self):
        self.tradingview_window = TradingView_Accounts(parent=None)
        self.tradingview_window.show()

    def open_ninja_trader_accounts(self):
        self.ninjatrader_window = NinjaTrader_Accounts(parent=None)
        self.ninjatrader_window.show()

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


class TradingView_Accounts(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.15), int(screen_height * 0.15))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.oldPos = None

        self.initUI()

    def initUI(self):
        self.tv_account_layout = QtWidgets.QVBoxLayout(self)
        self.tv_account_top = QVBoxLayout()
        self.tv_account_bottom = QVBoxLayout()
        if os.path.exists(TV_ACCOUNT_SETTINGS_PATH):
            self.loadAccounts()
        else:
            print('No account_settings.csv found')

        self.update_tv_account_button = QtWidgets.QPushButton("Add/Update Account with CSV File", clicked=self.open_file_dialog)
        self.tv_account_bottom.addWidget(self.update_tv_account_button)

        self.close_tv_account_button = QtWidgets.QPushButton("Close", clicked=self.close)
        self.tv_account_bottom.addWidget(self.close_tv_account_button)
        self.tv_account_layout.addLayout(self.tv_account_top)
        self.tv_account_layout.addLayout(self.tv_account_bottom)
        self.setLayout(self.tv_account_layout)

    def loadAccounts(self):
        self.accounts_listbox = QtWidgets.QListWidget()
        self.accounts_listbox.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.show_tv_account_button = QtWidgets.QPushButton("Show Account", clicked=self.show_accounts)
        self.tv_account_bottom.addWidget(self.show_tv_account_button)
        self.hide_tv_account_button = QtWidgets.QPushButton("Hide Account", clicked=self.hide_accounts)
        self.tv_account_bottom.addWidget(self.hide_tv_account_button)

        self.tv_account_top.addWidget(self.accounts_listbox)
        self.reload_accounts()

    def reload_accounts(self):
        self.accounts_listbox.clear()
        try:
            self.accounts_df = pd.read_csv(TV_ACCOUNT_SETTINGS_PATH)
            # Sort the accounts alphabetically
            self.accounts_df.sort_values(by='Account', inplace=True)
            # Load all accounts and mark hidden ones visually
            for index, row in self.accounts_df.iterrows():
                item = QtWidgets.QListWidgetItem(row['Account'])
                if row['Visibility'] == 'invisible':
                    item.setForeground(QtGui.QColor('gray'))  # Grey out hidden accounts
                self.accounts_listbox.addItem(item)
        except Exception as e:
            print("Failed to load accounts:", str(e))

    def hide_accounts(self):
        selected_items = self.accounts_listbox.selectedItems()
        for item in selected_items:
            account = item.text()
            # Update the DataFrame to set the account as invisible
            self.accounts_df.loc[self.accounts_df['Account'] == account, 'Visibility'] = 'invisible'
            item.setForeground(QtGui.QColor('gray'))  # Grey out the item visually

        # Save changes to the CSV
        self.accounts_df.to_csv(TV_ACCOUNT_SETTINGS_PATH, index=False)

    def show_accounts(self):
        selected_items = self.accounts_listbox.selectedItems()
        for item in selected_items:
            account = item.text()
            # Update the DataFrame to set the account as visible
            self.accounts_df.loc[self.accounts_df['Account'] == account, 'Visibility'] = 'visible'
            item.setForeground(QtGui.QColor('black'))  # Restore item color

        # Save changes to the CSV
        self.accounts_df.to_csv(TV_ACCOUNT_SETTINGS_PATH, index=False)

    def open_file_dialog(self):
        # Options for the file dialog
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a CSV file", "",
                                                             "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            try:
                account_name = os.path.basename(file_name)
                update_with_tradingview_data(file_name, account_name)
                self.loadAccounts()
            except Exception as e:
                print(f"Error processing file: {e}")


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


class NinjaTrader_Accounts(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.15), int(screen_height * 0.15))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.oldPos = None

        self.initUI()

    def initUI(self):
        self.nt_account_layout = QtWidgets.QVBoxLayout(self)
        self.nt_account_top = QVBoxLayout()
        self.nt_account_bottom = QVBoxLayout()
        if os.path.exists(NT_ACCOUNT_SETTINGS_PATH):
            self.loadAccounts()
        else:
            print('No account_settings.csv found')

        self.update_nt_account_button = QtWidgets.QPushButton("Add/Update Account(s) with CSV File", clicked=self.open_file_dialog)
        self.nt_account_bottom.addWidget(self.update_nt_account_button)

        self.close_nt_account_button = QtWidgets.QPushButton("Close", clicked=self.close)
        self.nt_account_bottom.addWidget(self.close_nt_account_button)

        self.nt_account_layout.addLayout(self.nt_account_top)
        self.nt_account_layout.addLayout(self.nt_account_bottom)

        self.setLayout(self.nt_account_layout)

    def loadAccounts(self):
        self.accounts_listbox = QtWidgets.QListWidget()
        self.accounts_listbox.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.show_nt_account_button = QtWidgets.QPushButton("Show Account", clicked=self.show_accounts)
        self.nt_account_bottom.addWidget(self.show_nt_account_button)
        self.hide_nt_account_button = QtWidgets.QPushButton("Hide Account", clicked=self.hide_accounts)
        self.nt_account_bottom.addWidget(self.hide_nt_account_button)

        self.nt_account_top.addWidget(self.accounts_listbox)
        self.reload_accounts()

    def reload_accounts(self):
        self.accounts_listbox.clear()
        try:
            self.accounts_df = pd.read_csv(NT_ACCOUNT_SETTINGS_PATH)
            # Sort the accounts alphabetically
            self.accounts_df.sort_values(by='Account', inplace=True)
            # Load all accounts and mark hidden ones visually
            for index, row in self.accounts_df.iterrows():
                item = QtWidgets.QListWidgetItem(row['Account'])
                if row['Visibility'] == 'invisible':
                    item.setForeground(QtGui.QColor('gray'))  # Grey out hidden accounts
                self.accounts_listbox.addItem(item)
        except Exception as e:
            print("Failed to load accounts:", str(e))

    def hide_accounts(self):
        selected_items = self.accounts_listbox.selectedItems()
        for item in selected_items:
            account = item.text()
            # Update the DataFrame to set the account as invisible
            self.accounts_df.loc[self.accounts_df['Account'] == account, 'Visibility'] = 'invisible'
            item.setForeground(QtGui.QColor('gray'))  # Grey out the item visually

        # Save changes to the CSV
        self.accounts_df.to_csv(NT_ACCOUNT_SETTINGS_PATH, index=False)

    def show_accounts(self):
        selected_items = self.accounts_listbox.selectedItems()
        for item in selected_items:
            account = item.text()
            # Update the DataFrame to set the account as visible
            self.accounts_df.loc[self.accounts_df['Account'] == account, 'Visibility'] = 'visible'
            item.setForeground(QtGui.QColor('black'))  # Restore item color

        # Save changes to the CSV
        self.accounts_df.to_csv(NT_ACCOUNT_SETTINGS_PATH, index=False)

    def open_file_dialog(self):
        # Options for the file dialog
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a CSV file", "",
                                                             "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            try:
                update_with_new_ninja_data(file_name)
                self.loadAccounts()
            except Exception as e:
                print(f"Error processing file: {e}")



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


