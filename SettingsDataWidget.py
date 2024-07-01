import pandas as pd
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from functions import NT_ACCOUNT_SETTINGS_PATH, TV_ACCOUNT_SETTINGS_PATH
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SettingsWidget(QWidget):
    closed = QtCore.pyqtSignal()
    reloadPressed = QtCore.pyqtSignal()
    def __init__(self, selected_account, data_path, account_type='NinjaTrader'):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Account Settings")

        self.initUI()
        self.oldPos = None
        self.selected_account = selected_account
        self.account_type = account_type
        if self.account_type == 'TradingView':
            self.data_settings = pd.read_csv(data_path)
            self.account_settings_path = TV_ACCOUNT_SETTINGS_PATH
        elif self.account_type == 'NinjaTrader':
            self.data_settings = data_path
            self.account_settings_path = NT_ACCOUNT_SETTINGS_PATH

    def initUI(self):
        # Main layout
        self.layout = QVBoxLayout(self)

        # Top frame with close and minimize buttons
        self.top_frame = QFrame(self)
        self.top_layout = QVBoxLayout(self.top_frame)
        self.close_button = QPushButton(self)
        close_icon = QtGui.QIcon()
        close_icon.addPixmap(QtGui.QPixmap(resource_path("resources/close.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close_button.setIcon(close_icon)

        self.reload_button = QtWidgets.QPushButton(self, clicked=self.onReloadButtonPress)
        reload_icon = QtGui.QIcon()
        reload_icon.addPixmap(QtGui.QPixmap(resource_path("resources/reload.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.reload_button.setIcon(reload_icon)

        self.top_layout.addWidget(self.close_button)
        self.top_layout.addWidget(self.reload_button)
        self.top_frame.setLayout(self.top_layout)

        # Middle frame with checkbox and slider
        self.middle_frame = QFrame(self)
        self.middle_layout = QHBoxLayout(self.middle_frame)

        self.selections_frame = QFrame(self)
        self.selections_frame_layout = QVBoxLayout(self.selections_frame)


        self.selection_label = QLabel("< Select account size\nBreak-even Threshold\n(Pips)\nV")
        self.selection_label.setAlignment(Qt.AlignCenter)
        self.threshold_box = QSpinBox(self)


        self.selections_frame_layout.addWidget(self.selection_label)
        self.selections_frame_layout.addWidget(self.threshold_box)

        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setMinimum(1)
        self.slider.setMaximum(7)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.sliderReleased.connect(self.onSliderRelease)

        # Labels layout
        self.labels_layout = QVBoxLayout()
        self.labels = {}
        self.slider_labels = {
            1: 25,
            2: 50,
            3: 75,
            4: 100,
            5: 150,
            6: 250,
            7: 300
        }
        self.slider_labels_reverse = {
            1: 300,
            2: 250,
            3: 150,
            4: 100,
            5: 75,
            6: 50,
            7: 25
        }
        for i in range(1, 8):
            label = QLabel(str(self.slider_labels_reverse[i]) + "k", self)
            label.setAlignment(Qt.AlignCenter)
            self.labels[i] = label
            self.labels_layout.addWidget(label)

        self.middle_layout.addWidget(self.slider)
        self.middle_layout.addLayout(self.labels_layout)
        self.middle_layout.addWidget(self.selections_frame)
        self.middle_frame.setLayout(self.middle_layout)


        # Add frames to the main layout
        self.layout.addWidget(self.top_frame)
        self.layout.addWidget(self.middle_frame)

        # Window settings
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        self.setGeometry(100, 100, int(screen_width * 0.1), int(screen_height * 0.2))
        self.show()

        # Connect button actions
        self.close_button.clicked.connect(self.close)

        # Apply stylesheet for the black outline
        self.setStyleSheet("""
            QWidget {
                border: 2px solid black;
            }
        """)

    def update_values(self):
        self.update_slider_position()


    def update_slider_position(self):
        try:
            if self.selected_account is None:
                return
            account_row = self.data_settings.loc[self.data_settings['Account'] == self.selected_account]

            if not account_row['ASize'].empty:
                asize = account_row['ASize'].values[0]
                for key, value in self.slider_labels.items():
                    if value == asize:
                        self.slider.setValue(key)
                        break
            else:
                self.slider.setValue(1)
        except Exception as e:
            print(f'Failed updating slider position because: {e}')

    def onReloadButtonPress(self):
        value = self.slider.value()
        asize = self.slider_labels[value]
        pips = self.threshold_box.value()

        data = self.data_settings
        data.loc[data['Account'] == self.selected_account, 'ASize'] = asize
        data.loc[data['Account'] == self.selected_account, 'BeT'] = pips

        data.to_csv(self.account_settings_path, index=False)
        print(f"Updated account_settings.csv. Account Size: {asize}k. Threshold: {pips}")
        self.reloadPressed.emit()

    def closeEvent(self, event):
        self.closed.emit()  # Emit the closed signal
        event.accept()

    def onSliderRelease(self):
        value = self.slider.value()
        print(self.slider_labels[value])
        return self.slider_labels[value]


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