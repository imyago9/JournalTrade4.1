from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import *
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import mplcursors
import matplotlib.dates as mdates
from custom_calendar import CustomCalendar
from SettingsApexDataWidget import SettingsWidget
from TradeImageWidget import ScreenshotPrompt, ScreenshotUpload, ScreenshotDisplay
import os
import json
import re
from functions import use_data_path, visibility_file_path, screenshots_path
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ApexDataWidget(QDialog):
    def __init__(self, parent=None):
        super(ApexDataWidget, self).__init__(parent)

        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        self.setGeometry(100, 100, int(self.screen_width * 0.8), int(self.screen_height * 0.7))

        self.setWindowTitle("Apex Account(s) Data")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setupUi()
        self._is_moving = False
        self._start_pos = None
        self.current_date = QDate.currentDate()
        self.targets = {25: 1500, 50: 3000, 75: 4250, 100: 6000, 150: 9000, 250: 15000, 300: 20000}
        self.stop_losses = {25: 1500, 50: 2500, 75: 2750, 100: 3000, 150: 5000, 250: 6500, 300: 7500}
        self.mapping_file = os.path.join(screenshots_path, 'screenshot_mapping.json')
        self.screenshots = self.load_screenshots()

    def load_screenshots(self):
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load screenshots: {e}")
        return {}

    def setupUi(self):
        self.main_layout_vertical = QVBoxLayout(self)
        self.setupTopFrame()
        self.setupBottomFrame()
        self.main_layout_vertical.addWidget(self.top_frame)
        self.main_layout_vertical.addWidget(self.bottom_frame)
        self.accountselection_comboBox.currentIndexChanged.connect(self.display_selected_account)
        self.first_dateEdit.dateChanged.connect(self.updateWithDate)
        self.second_dateEdit.dateChanged.connect(self.updateWithDate)

    def setupTopFrame(self):
        self.top_frame = QFrame()
        self.top_frame.setStyleSheet("border: 2px solid black;")
        self.top_frame.setMaximumHeight(int(self.screen_height * 0.05))
        self.top_frame_layout_horizontal = QHBoxLayout(self.top_frame)
        self.top_frame_layout_horizontal.setContentsMargins(0, 0, 0, 0)
        self.top_frame_layout_horizontal.setSpacing(0)
        self.setupDataManagementFrame()
        self.setupTopFrameTitle()
        self.setupWindowButtonsFrame()
        self.top_frame_layout_horizontal.addWidget(self.data_management_frame)
        self.top_frame_layout_horizontal.addWidget(self.top_frame_title)
        self.top_frame_layout_horizontal.addWidget(self.window_buttons_frame)

    def setupDataManagementFrame(self):
        self.data_management_frame = QFrame(self.top_frame)
        self.data_management_frame_layout_horizontal = QHBoxLayout(self.data_management_frame)
        self.first_dateEdit = QDateEdit(self.data_management_frame)
        self.first_dateEdit.setCalendarPopup(True)
        self.second_dateEdit = QDateEdit(self.data_management_frame)
        self.second_dateEdit.setCalendarPopup(True)
        self.accountselection_comboBox = QComboBox(self.data_management_frame)
        self.account_settings_button = QPushButton(self.data_management_frame, clicked=self.open_settings_widget)
        account_settings_icon = QtGui.QIcon()
        account_settings_icon.addPixmap(QtGui.QPixmap(resource_path("resources/settings-v-svgrepo-com.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.account_settings_button.setIcon(account_settings_icon)
        self.load_apex_accounts()
        self.data_management_frame_layout_horizontal.addWidget(self.first_dateEdit)
        self.data_management_frame_layout_horizontal.addWidget(self.second_dateEdit)
        self.data_management_frame_layout_horizontal.addWidget(self.accountselection_comboBox)
        self.data_management_frame_layout_horizontal.addWidget(self.account_settings_button)

    def setupTopFrameTitle(self):
        self.top_frame_title = QLabel("Apex Account(s) Data")
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.top_frame_title.setFont(font)
        self.top_frame_title.setAlignment(QtCore.Qt.AlignCenter)

    def setupWindowButtonsFrame(self):
        self.window_buttons_frame = QFrame(self.top_frame)
        self.window_buttons_frame_layout_horizontal = QHBoxLayout(self.window_buttons_frame)
        self.minimize_button = QPushButton(self.window_buttons_frame, clicked=self.showMinimized)
        minimize_icon = QtGui.QIcon()
        minimize_icon.addPixmap(QtGui.QPixmap(resource_path("resources/minimize.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.minimize_button.setIcon(minimize_icon)
        self.close_button = QPushButton(self.window_buttons_frame, clicked=self.close)
        close_icon = QtGui.QIcon()
        close_icon.addPixmap(QtGui.QPixmap(resource_path("resources/close.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close_button.setIcon(close_icon)
        self.window_buttons_frame_layout_horizontal.addWidget(self.minimize_button)
        self.window_buttons_frame_layout_horizontal.addWidget(self.close_button)

    def setupBottomFrame(self):
        self.bottom_frame = QFrame()
        self.bottom_frame_layout_vertical = QVBoxLayout(self.bottom_frame)
        self.stats_frame = self.createStatsFrame()
        self.stats_frame.setMaximumHeight(int(self.screen_height * 0.2))
        self.graphs_frame = self.createGraphsFrame()
        self.graphs_frame.setMaximumHeight(int(self.screen_height * 0.55))
        self.bottom_frame_layout_vertical.addWidget(self.stats_frame)
        self.bottom_frame_layout_vertical.addWidget(self.graphs_frame)

    def createStatsFrame(self):
        stats_frame = QFrame(self.bottom_frame)
        stats_frame_layout_horizontal = QHBoxLayout(stats_frame)
        self.first_stats_frame, self.first_stats_label = self.createStatsBox()
        self.second_stats_frame, self.second_stats_label = self.createStatsBox()
        self.third_stats_frame, self.third_stats_label = self.createStatsBox()
        self.fourth_stats_frame, self.fourth_stats_label = self.createStatsBox()
        stats_frame_layout_horizontal.addWidget(self.first_stats_frame)
        stats_frame_layout_horizontal.addWidget(self.second_stats_frame)
        stats_frame_layout_horizontal.addWidget(self.third_stats_frame)
        stats_frame_layout_horizontal.addWidget(self.fourth_stats_frame)
        return stats_frame

    def createStatsBox(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        label = QLabel(frame)
        layout.addWidget(label)
        frame.setStyleSheet("border: 2px solid black;")
        return frame, label

    def createGraphsFrame(self):
        graphs_frame = QFrame(self.bottom_frame)
        graphs_frame.setStyleSheet("border: 2px solid black;")
        horizontal_layout = QHBoxLayout(graphs_frame)
        self.first_graph_frame = QFrame(graphs_frame)
        self.second_graph_frame = QFrame(graphs_frame)
        self.third_graph_frame = QFrame(graphs_frame)
        self.first_graph_frame.setLayout(QVBoxLayout())
        self.second_graph_frame.setLayout(QVBoxLayout())
        self.third_graph_frame.setLayout(QVBoxLayout())
        horizontal_layout.addWidget(self.first_graph_frame)
        horizontal_layout.addWidget(self.second_graph_frame)
        horizontal_layout.addWidget(self.third_graph_frame)
        return graphs_frame

    def load_apex_accounts(self):
        try:
            self.data = pd.read_csv(use_data_path)
            self.data_settings = pd.read_csv(visibility_file_path)
            accounts = self.data['Account'].unique()
            apex_accounts = sorted([account for account in accounts if 'Apex' in account])
            visible_accounts = self.data_settings[self.data_settings['Visibility'] == 'visible']['Account']
            visible_apex_accounts = [account for account in apex_accounts if account in visible_accounts.values]
            self.accountselection_comboBox.clear()
            self.accountselection_comboBox.addItems(visible_apex_accounts)
            self.accountselection_comboBox.setCurrentIndex(-1)
            if self.accountselection_comboBox.currentText() == '':
                self.first_dateEdit.setEnabled(False)
                self.second_dateEdit.setEnabled(False)
        except Exception as e:
            print(f"Error loading accounts: {e}")

    def filter_data_by_date_range(self, data, start_date, end_date):
        data = data.copy()
        data['ExitT'] = pd.to_datetime(data['ExitT'], format="%Y-%m-%d %H:%M:%S")
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        data = data[(data['ExitT'] >= start_date) & (data['ExitT'] <= end_date)]
        data['ExitT'] = data['ExitT'].dt.strftime("%Y-%m-%d %H:%M:%S")
        return data

    def has_new_data(self, data):
        account_row = self.data_settings.loc[self.data_settings['Account'] == self.selected_account]
        if account_row.empty:
            return False

        last_updated_profit = account_row['LastUpdatedProfit'].values[0]
        current_cumulative_profit = data['Profit'].sum()

        return current_cumulative_profit != last_updated_profit

    def display_selected_account(self):
        try:
            self.selected_account = self.accountselection_comboBox.currentText()
            self.account_data = self.data[self.data['Account'] == self.selected_account]
            print(f"Selected Account: {self.selected_account}")  # Debug statement
            if self.account_data.empty:
                print("Account data is empty")
                return
            self.updateDateEdits()
            self.updateStatsLabels(self.account_data)
            self.plot_line_graph(self.account_data)
            self.plot_trade_performance(self.account_data)
            self.plot_calendar(self.account_data)
        except Exception as e:
            print(f"Error displaying selected account: {e}")

    def updateWithDate(self):
        start_date = self.first_dateEdit.date().toString("yyyy-MM-dd")
        end_date = self.second_dateEdit.date().toString("yyyy-MM-dd")
        filtered_data = self.filter_data_by_date_range(self.account_data, start_date, end_date)
        self.updateStatsLabels(filtered_data)
        self.plot_line_graph(filtered_data)
        self.plot_trade_performance(filtered_data)
        self.plot_calendar(filtered_data)

    def updateDateEdits(self):
        self.first_dateEdit.setEnabled(False)
        self.second_dateEdit.setEnabled(False)
        self.first_dateEdit.clearMaximumDate()
        self.first_dateEdit.clearMinimumDate()
        self.second_dateEdit.clearMaximumDate()
        self.second_dateEdit.clearMinimumDate()
        self.account_row = self.data_settings.loc[self.data_settings['Account'] == self.selected_account]
        account_first_date = pd.to_datetime(self.account_data['EntryT']).min()
        account_last_date = pd.to_datetime(self.account_data['ExitT']).max()
        if pd.isnull(account_first_date) or pd.isnull(account_last_date):
            print("Invalid date range")
            return
        self.first_dateEdit.blockSignals(True)
        self.second_dateEdit.blockSignals(True)
        self.first_dateEdit.setDate(QDate(account_first_date.year, account_first_date.month, account_first_date.day))
        self.second_dateEdit.setDate(QDate(account_last_date.year, account_last_date.month, account_last_date.day))
        self.first_dateEdit.setMinimumDate(QDate(account_first_date.year, account_first_date.month, account_first_date.day))
        self.first_dateEdit.setMaximumDate(QDate(account_last_date.year, account_last_date.month, account_last_date.day))
        self.second_dateEdit.setMinimumDate(QDate(account_first_date.year, account_first_date.month, account_first_date.day))
        self.second_dateEdit.setMaximumDate(QDate(account_last_date.year, account_last_date.month, account_last_date.day))
        self.first_dateEdit.blockSignals(False)
        self.second_dateEdit.blockSignals(False)
        self.first_dateEdit.setEnabled(True)
        self.second_dateEdit.setEnabled(True)

    def updateStatsLabels(self, data):
        pips = self.account_row['BeT'].values[0]
        grouped_data = data.groupby('EntryT').agg({'Profit': 'sum', 'LorS': 'first', 'Instrument': 'first'}).reset_index()

        def get_threshold(instrument):
            if 'MES' in instrument:
                return pips * 1.25
            elif 'ES' in instrument:
                return pips * 12.5
            return 0

        w_be_l = grouped_data.apply(lambda row: 'L' if row['Profit'] < 0 else ('B' if row['Profit'] <= get_threshold(row['Instrument']) else 'W'), axis=1)
        grouped_data['Result'] = w_be_l
        net_pnl = grouped_data['Profit'].sum()
        total_trades = len(grouped_data)
        self.total_trades = total_trades
        winning_trades = len(grouped_data[grouped_data['Result'] == 'W'])
        losing_trades = len(grouped_data[grouped_data['Result'] == 'L'])
        break_even_trades = len(grouped_data[grouped_data['Result'] == 'B'])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        loss_rate = (losing_trades / total_trades) * 100 if total_trades > 0 else 0
        break_even_rate = (break_even_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_win = grouped_data[grouped_data['Result'] == 'W']['Profit'].mean()
        avg_loss = grouped_data[grouped_data['Result'] == 'L']['Profit'].mean()
        avg_rr = avg_win/np.abs(avg_loss)
        self.first_stats_label.setText(f"Net Profit: ${net_pnl:.2f}")
        self.second_stats_label.setText(f"Win Rate: {win_rate:.2f}%\nLoss Rate: {loss_rate:.2f}%\nB/e Rate: {break_even_rate:.2f}%")
        self.third_stats_label.setText(f"Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f} | Avg RR ratio: {avg_rr:.2f}")
        self.fourth_stats_label.setText(f"Number of Trades: {total_trades}")

    def plot_line_graph(self, data):
        try:
            self.clearLayout(self.first_graph_frame.layout())
            data.loc[:, 'EntryT'] = pd.to_datetime(data['EntryT'])
            cumulative_progress = data.groupby('EntryT')['Profit'].sum().cumsum()
            fig, ax = plt.subplots()
            fig.patch.set_facecolor('#F0F0F0')
            ax.set_facecolor('#F0F0F0')
            line, = ax.plot(cumulative_progress.index, cumulative_progress, color='black', label='Cumulative Profit', linewidth=0.4)
            ax.scatter(cumulative_progress.index, cumulative_progress, color='black', s=6, zorder=5, label='Trades')
            ax.grid(False)
            ax.axhline(0, color='black', linestyle='--', linewidth=0.4, label='$0')
            cursor = mplcursors.cursor(line, hover=True)
            cursor.connect("add", lambda sel: sel.annotation.set_text(f"Date: {cumulative_progress.index[int(sel.index)].strftime('%m/%d - %H:%M')}\nProfit: {cumulative_progress.iloc[int(sel.index)]:.2f}"))
            cursor.connect("add", lambda sel: self.annotation_color(sel))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
            ax.set_title('')
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.legend()
            fig.tight_layout(pad=0, h_pad=0, w_pad=0)
            ax.set_title("Profit Across Trades")
            canvas = FigureCanvas(fig)
            self.first_graph_frame.layout().addWidget(canvas)
        except Exception as e:
            print(f"Error plotting graph: {e}")

    def plot_trade_performance(self, data):
        try:
            self.clearLayout(self.second_graph_frame.layout())
            filtered_data = data.copy()
            filtered_data.loc[:, 'EntryT'] = pd.to_datetime(filtered_data['EntryT'], errors='coerce')
            if filtered_data.empty:
                label = QLabel("No trades were made in this date range.")
                self.second_graph_frame.layout().addWidget(label)
                return
            grouped_data = filtered_data.groupby('EntryT').agg(Profit=('Profit', 'sum'), Qty=('Qty', 'sum'), LorS=('LorS', 'first'), Account=('Account', 'first')).reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor('#F0F0F0')
            ax.set_facecolor('#F0F0F0')
            bars = ax.bar(grouped_data.index, grouped_data['Profit'], color=np.where(grouped_data['Profit'] > 0, 'green', 'red'))
            cursor = mplcursors.cursor(bars, hover=True)
            cursor.connect("add", lambda sel: self.annotate_bar(sel, grouped_data))
            fig.canvas.mpl_connect('button_press_event', lambda event: self.on_click(event, bars, grouped_data))
            ax.set_title('Trade Performance')
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.axhline(0, color='grey', linewidth=0.8)
            plt.tight_layout()
            canvas = FigureCanvas(fig)
            self.second_graph_frame.layout().addWidget(canvas)
        except Exception as e:
            print(f"Error plotting trade performance: {e}")

    def on_click(self, event, bars, grouped_data):
        for i, bar in enumerate(bars):
            if bar.contains(event)[0]:
                selected_data = grouped_data.iloc[i]
                trade_id = f"{selected_data['Account']}_{selected_data['EntryT']}"
                sanitized_trade_id = re.sub(r'[<>:"/\\|?*]', '_', trade_id)
                if sanitized_trade_id in self.screenshots:
                    self.show_screenshot(self.screenshots[sanitized_trade_id])
                else:
                    self.prompt_add_screenshot(sanitized_trade_id, selected_data)
                break

    def annotate_bar(self, sel, grouped_data):
        sel.annotation.set_text(
            f"Date: {pd.to_datetime(grouped_data.iloc[sel.index]['EntryT']).strftime('%m/%d - %H:%M')}\n" +
            f"RR: {grouped_data.iloc[sel.index]['Profit']:.2f}\n" +
            f"Qty: {grouped_data.iloc[sel.index]['Qty']}\n" +
            f"LorS: {grouped_data.iloc[sel.index]['LorS']}\n" +
            f"Account: {grouped_data.iloc[sel.index]['Account']}"
        )
        sel.annotation.get_bbox_patch().set(fc='black', alpha=0.6)
        sel.annotation.get_bbox_patch().set_edgecolor('none')
        sel.annotation.set_color('white')

    def prompt_add_screenshot(self, trade_id, trade_info):
        dialog = ScreenshotPrompt(trade_info)
        if dialog.exec_() == QDialog.Accepted:
            upload_dialog = ScreenshotUpload(trade_info, trade_id)
            if upload_dialog.exec_() == QDialog.Accepted:
                self.screenshots[trade_id] = upload_dialog.screenshot_path
                self.save_screenshots()

    def show_screenshot(self, screenshot_path):
        dialog = ScreenshotDisplay(screenshot_path)
        dialog.exec_()

    def save_screenshots(self):
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.screenshots, f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save screenshots: {e}")

    def print_bar_info(self, selected_data):
        try:
            print(f"Bar clicked - Date: {pd.to_datetime(selected_data['EntryT']).strftime('%Y-%m-%d %H:%M')}, Profit: {selected_data['Profit']}, Qty: {selected_data['Qty']}, LorS: {selected_data['LorS']}, Account: {selected_data['Account']}")
        except Exception as e:
            print(f"Error printing bar info: {e}")

    def plot_calendar(self, data):
        try:
            for i in reversed(range(self.third_graph_frame.layout().count())):
                widget_to_remove = self.third_graph_frame.layout().itemAt(i).widget()
                if widget_to_remove:
                    self.third_graph_frame.layout().removeWidget(widget_to_remove)
                    widget_to_remove.setParent(None)
            self.calendar = CustomCalendar(parent=None)
            self.calendar.account_data = data
            self.update_calendar(data)
            self.third_graph_frame.layout().addWidget(self.calendar)
            self.show()
        except Exception as e:
            print(f"Error plotting calendar: {e}")

    def update_calendar(self, data):
        data = data.groupby('EntryT').agg({'Profit': 'sum', 'LorS': 'first'}).reset_index()
        data['EntryT'] = pd.to_datetime(data['EntryT'])
        data['Date'] = data['EntryT'].dt.date
        grouped_data = data.groupby('Date').agg({'Profit': 'sum', 'EntryT': 'count'}).rename(columns={'EntryT': 'Trades'}).reset_index()
        for index, row in grouped_data.iterrows():
            date = row['Date']
            if date.month == self.current_date.month() and date.year == self.current_date.year():
                day = date.day
                text = f"Profit: {row['Profit']}\nTrades: {row['Trades']}"
                self.calendar.setText(day, text)

    def open_settings_widget(self):
        if not self.accountselection_comboBox.currentIndex() == -1:
            self.settings_widget = SettingsWidget()
            self.settings_widget.selected_account = self.selected_account
            self.settings_widget.data_settings = self.data_settings
            self.settings_widget.update_values()
            self.settings_widget.closed.connect(self.enable_apex_data_widget)
            self.settings_widget.reloadPressed.connect(self.update_graph)
            self.settings_widget.show()
            self.setEnabled(False)

    def enable_apex_data_widget(self):
        self.setEnabled(True)

    def update_graph(self):
        self.display_selected_account()

    def annotation_color(self, sel):
        sel.annotation.get_bbox_patch().set(fc='black', alpha=0.6)
        sel.annotation.get_bbox_patch().set_edgecolor('none')
        sel.annotation.set_color('white')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._is_moving = True
            self._start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self._is_moving:
            self.move(self.pos() + event.pos() - self._start_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._is_moving = False

    def clearLayout(self, layout):
        plt.close()
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            if widget_to_remove:
                layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
