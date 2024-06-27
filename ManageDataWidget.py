from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import pyqtSignal
import pandas as pd
from functions import update_with_new_data, use_data_path, visibility_file_path


class ManageDataWidget(QtWidgets.QDialog):
    csv_uploaded = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Account Data")
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.15), int(screen_height * 0.4))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.initUI()

    def initUI(self):
        self.manageDataLayout = QtWidgets.QVBoxLayout(self)
        self.loadAccounts()

        # Show and Hide account buttons
        self.show_button = QtWidgets.QPushButton("Show Account", clicked=self.show_accounts)
        self.manageDataLayout.addWidget(self.show_button)

        self.hide_button = QtWidgets.QPushButton("Hide Account", clicked=self.hide_accounts)
        self.manageDataLayout.addWidget(self.hide_button)

        self.update_data_button = QtWidgets.QPushButton("Upload Broker CSV File", clicked=self.open_file_dialog)
        self.manageDataLayout.addWidget(self.update_data_button)

        self.close_button = QtWidgets.QPushButton("Close", clicked=self.close)
        self.manageDataLayout.addWidget(self.close_button)

        self.oldPos = None

    def open_file_dialog(self):
        # Options for the file dialog
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a CSV file", "",
                                                             "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            try:
                update_with_new_data(file_name)
                self.csv_uploaded.emit()  # Emit the signal after processing
                self.reload_accounts()
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

    def loadAccounts(self):
        self.accounts_listbox = QtWidgets.QListWidget()
        self.accounts_listbox.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.manageDataLayout.addWidget(self.accounts_listbox)
        self.reload_accounts()

    def reload_accounts(self):
        self.accounts_listbox.clear()
        try:
            self.accounts_df = pd.read_csv(visibility_file_path)
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
        self.accounts_df.to_csv(visibility_file_path, index=False)

    def show_accounts(self):
        selected_items = self.accounts_listbox.selectedItems()
        for item in selected_items:
            account = item.text()
            # Update the DataFrame to set the account as visible
            self.accounts_df.loc[self.accounts_df['Account'] == account, 'Visibility'] = 'visible'
            item.setForeground(QtGui.QColor('black'))  # Restore item color

        # Save changes to the CSV
        self.accounts_df.to_csv(visibility_file_path, index=False)
