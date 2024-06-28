import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtGui, QtCore
import os
from ManageDataWidget import ManageDataWidget
from NinjaTraderDataWidget import NinjaTraderDataWidget
from TradingViewDataWidget import TradingViewDataWidget

data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'data')

class SelectAccountBox(QDialog):
    def __init__(self, message, folders=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self.initUI(message, folders)
        self.oldPos = None

    def initUI(self, message, folders):
        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.folder_buttons = []
        if folders:
            for folder in folders:
                button = QPushButton(folder, self)
                button.clicked.connect(lambda _, f=folder: self.folder_selected(f))
                layout.addWidget(button)
                self.folder_buttons.append(button)
            close_button = QPushButton('Close', clicked=self.close)
            layout.addWidget(close_button)

        self.setLayout(layout)

    def folder_selected(self, folder):
        self.selected_folder = folder
        self.accept()

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
    def show_message(message, folders=None, parent=None):
        dialog = SelectAccountBox(message, folders, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted, getattr(dialog, 'selected_folder', None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("JournalTrade")

        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.3), int(screen_height * 0.05))

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

        self.view_data_button = QPushButton('View Data', clicked=self.open_view_data_widget)
        view_data_icon = QtGui.QIcon()
        view_data_icon.addPixmap(QtGui.QPixmap(resource_path("resources/viewdata.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.view_data_button.setIcon(view_data_icon)

        self.top_layout.addWidget(self.manage_data_button)
        self.top_layout.addWidget(self.view_data_button)
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

        self.close_button.clicked.connect(sys.exit)
        self.minimize_button.clicked.connect(self.showMinimized)

        # Apply stylesheet for the black outline
        self.setStyleSheet("""
            QWidget {
                border: 2px solid black;
            }
        """)


    def open_manage_data_widget(self):
        self.manage_widget = ManageDataWidget(parent=None)
        self.manage_widget.show()

    def open_view_data_widget(self):
        folders = self.list_folders_in_directory(data_path)

        if len(folders) == 1:
            self.check_folder_selected_and_load(folders[0])
        elif len(folders) > 1:
            reply, selected_folder = SelectAccountBox.show_message('Select which type of account(s) you wish to see:', folders, self)
            if reply:
                self.check_folder_selected_and_load(selected_folder)
        else:
            print("No folders found.")

    def list_folders_in_directory(self, directory):
        return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

    def check_folder_selected_and_load(self, selected_folder):
        if selected_folder == 'NinjaTrader':
            self.ninjatrader_data_widget = NinjaTraderDataWidget(parent=None)
            self.ninjatrader_data_widget.show()
        elif selected_folder == 'TradingView':
            self.tradingview_widget = TradingViewDataWidget(parent=None)
            self.tradingview_widget.show()


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
