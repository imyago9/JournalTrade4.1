import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView, QAbstractItemView, QFileDialog, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtGui
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import os
from functions import update_with_new_data
from ManageDataWidget import ManageDataWidget
from ApexDataWidget import ApexDataWidget
from functions import use_data_path
import requests

GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'

def get_github_version(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error fetching version from GitHub: {e}")
        return None

def get_local_version(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.check_for_updates()
        self.check_data()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("JournalTrade")

        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.45), int(screen_height * 0.2))

        self._is_dragging = False
        self._drag_start_position = QPoint()


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.top_frame = QWidget()
        self.top_layout = QHBoxLayout(self.top_frame)

        self.manage_data_button = QPushButton('Manage Data', clicked=self.open_manage_data_widget)
        manage_data_icon = QtGui.QIcon()
        manage_data_icon.addPixmap(QtGui.QPixmap(resource_path("resources/managedata.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.manage_data_button.setIcon(manage_data_icon)

        self.view_data_button = QPushButton('View Data')
        view_data_icon = QtGui.QIcon()
        view_data_icon.addPixmap(QtGui.QPixmap(resource_path("resources/viewdata.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.view_data_button.setIcon(view_data_icon)

        self.apex_data_button = QPushButton('Apex Account(s) Data', clicked=self.open_apex_data_widget)
        apex_data_icon = QtGui.QIcon()
        apex_data_icon.addPixmap(QtGui.QPixmap(resource_path("resources/apexaccounts.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.apex_data_button.setIcon(apex_data_icon)

        self.top_layout.addWidget(self.manage_data_button)
        self.top_layout.addWidget(self.view_data_button)
        self.top_layout.addWidget(self.apex_data_button)
        self.top_layout.addStretch(1)

        self.minimize_button = QPushButton()
        minimize_icon = QtGui.QIcon()
        minimize_icon.addPixmap(QtGui.QPixmap(resource_path("resources/minimize.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.minimize_button.setIcon(minimize_icon)

        self.close_button = QPushButton()
        close_icon = QtGui.QIcon()
        close_icon.addPixmap(QtGui.QPixmap(resource_path("resources/close.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close_button.setIcon(close_icon)

        self.top_layout.addWidget(self.minimize_button)
        self.top_layout.addWidget(self.close_button)

        self.layout.addWidget(self.top_frame)

        # Bottom Frame with QTreeView
        self.bottom_frame = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_frame)

        self.tree_view = QTreeView()
        self.load_data_into_tree_view()

        self.bottom_layout.addWidget(self.tree_view)

        self.layout.addWidget(self.bottom_frame)

        self.close_button.clicked.connect(sys.exit)
        self.minimize_button.clicked.connect(self.showMinimized)

        # Apply stylesheet for the black outline
        self.setStyleSheet("""
            QWidget {
                border: 2px solid black;
            }
        """)

    def check_for_updates(self):
        github_version = get_github_version(GITHUB_REPO_URL)
        local_version = get_local_version(os.path.join(os.getenv('LOCALAPPDATA'), 'JournalTrade', 'version.txt'))

        if github_version and local_version and github_version != local_version:
            QMessageBox.information(self, 'Update Available', 'A new version of JournalTrade is available. Please '
                                                              'close the application and run InstallerUpdater.exe.')

    def check_data(self):
        if not os.path.exists(use_data_path):
            QMessageBox.warning(self, "File Not Found", "To run the app you need to enter a csv file from "
                                                        "NinjaTrader. On NinjaTrader, select the following "
                                                        "columns:\n*Instrument,"
                                                        "Account,Market pos.,Qty,Entry price,Exit price,Entry time,"
                                                        "Exit time,Profit,Commission*")
            file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
            if not file_path:
                sys.exit()
            else:
                update_with_new_data(file_path)


    def load_data_into_tree_view(self):
        data = pd.read_csv(use_data_path)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(data.columns.tolist())

        for row in data.itertuples(index=False):
            items = [QStandardItem(str(field)) for field in row]
            model.appendRow(items)

        self.tree_view.setModel(model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)


    def update_tree_view(self):
        self.load_data_into_tree_view()

    def open_manage_data_widget(self):
        self.manage_widget = ManageDataWidget(parent=None)
        self.manage_widget.csv_uploaded.connect(self.update_tree_view)
        self.manage_widget.show()

    def open_apex_data_widget(self):
        self.apex_widget = ApexDataWidget(parent=None)
        self.apex_widget.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPos() - self._drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_stylesheet(app):
    stylesheet_path = resource_path('resources/style.qss')
    with open(stylesheet_path, "r") as file:
        app.setStyleSheet(file.read())

def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
