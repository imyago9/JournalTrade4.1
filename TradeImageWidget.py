import os
import json
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint
import pandas as pd
import shutil
import re

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

class ScreenshotPrompt(QDialog):
    def __init__(self, trade_info, parent=None):
        super(ScreenshotPrompt, self).__init__(parent)
        self.trade_info = trade_info
        self.drag_pos = QPoint()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 300, 100)
        self.center()

        layout = QVBoxLayout()

        trade_info = self.trade_info
        info = (
            f"Account: {trade_info['Account']}\n"
            f"Date: {pd.to_datetime(trade_info['EntryT']).strftime('%Y-%m-%d %H:%M')}\n"
            f"P&L: {trade_info['Profit']}\n"
            f"# Contracts: {trade_info['Qty']}\n"
            f"Long or Short: {trade_info['LorS']}"
        )
        label = QLabel(f"Do you wish to add a screenshot for this trade?\n{info}")
        layout.addWidget(label)

        button_layout = QHBoxLayout()

        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(self.accept)
        button_layout.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(no_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def center(self):
        frame_geom = self.frameGeometry()
        parent_pos = self.parent().frameGeometry().center() if self.parent() else QDesktopWidget().availableGeometry().center()
        frame_geom.moveCenter(parent_pos)
        self.move(frame_geom.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()


class ScreenshotUpload(QDialog):
    def __init__(self, trade_info, trade_id, screenshots_dir='resources/screenshots', parent=None):
        super(ScreenshotUpload, self).__init__(parent)
        self.trade_info = trade_info
        self.trade_id = trade_id
        self.screenshots_dir = screenshots_dir
        self.mapping_file = os.path.join(screenshots_dir, 'screenshot_mapping.json')
        self.screenshot_path = None
        self.drag_pos = QPoint()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 200)
        self.center()

        layout = QVBoxLayout()

        trade_info = self.trade_info
        info = (
            f"Account: {trade_info['Account']}\n"
            f"Date: {pd.to_datetime(trade_info['EntryT']).strftime('%Y-%m-%d %H:%M')}\n"
            f"P&L: {trade_info['Profit']}\n"
            f"# Contracts: {trade_info['Qty']}\n"
            f"Long or Short: {trade_info['LorS']}"
        )
        label = QLabel(f"Upload screenshot for trade:\n{info}")
        layout.addWidget(label)

        self.file_path = QLineEdit()
        layout.addWidget(self.file_path)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)


        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def center(self):
        frame_geom = self.frameGeometry()
        parent_pos = self.parent().frameGeometry().center() if self.parent() else QDesktopWidget().availableGeometry().center()
        frame_geom.moveCenter(parent_pos)
        self.move(frame_geom.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def browse_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Screenshot", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.file_path.setText(file_path)
            self.upload_file()

    def upload_file(self):
        source_path = self.file_path.text()
        if os.path.exists(source_path):
            try:
                os.makedirs(self.screenshots_dir, exist_ok=True)
                sanitized_trade_id = re.sub(r'[<>:"/\\|?*]', '_', self.trade_id)
                self.screenshot_path = os.path.join(self.screenshots_dir, f"{sanitized_trade_id}.png")
                shutil.copy(source_path, self.screenshot_path)
                self.update_mapping_file()
                self.accept()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to upload screenshot: {e}")
        else:
            QMessageBox.warning(self, "Error", "Invalid file path")

    def update_mapping_file(self):
        mapping = {}
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load mapping file: {e}")

        sanitized_trade_id = re.sub(r'[<>:"/\\|?*]', '_', self.trade_id)
        mapping[sanitized_trade_id] = self.screenshot_path

        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping, f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save mapping file: {e}")

    def update_mapping_file(self):
        mapping = {}
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load mapping file: {e}")

        mapping[self.trade_id] = self.screenshot_path

        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping, f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save mapping file: {e}")


class ScreenshotDisplay(QDialog):
    def __init__(self, screenshot_path, parent=None):
        super(ScreenshotDisplay, self).__init__(parent)
        self.screenshot_path = screenshot_path
        self.drag_pos = QPoint()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 600)
        self.center()

        layout = QVBoxLayout()

        label = QLabel()
        pixmap = QtGui.QPixmap(self.screenshot_path)
        label.setPixmap(pixmap)
        layout.addWidget(label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def center(self):
        frame_geom = self.frameGeometry()
        parent_pos = self.parent().frameGeometry().center() if self.parent() else QDesktopWidget().availableGeometry().center()
        frame_geom.moveCenter(parent_pos)
        self.move(frame_geom.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()