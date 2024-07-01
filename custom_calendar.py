from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
import pandas as pd

class CustomCalendar(QWidget):
    def __init__(self, account_type='NinjaTrader', parent=None):
        super(CustomCalendar, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.navigation_layout = QHBoxLayout()
        self.account_type = account_type

        self.prev_button = QPushButton("<", self)
        self.prev_button.clicked.connect(self.prevMonth)
        self.navigation_layout.addWidget(self.prev_button)

        self.current_month_label = QLabel(self)
        self.navigation_layout.addWidget(self.current_month_label)

        self.next_button = QPushButton(">", self)
        self.next_button.clicked.connect(self.nextMonth)
        self.navigation_layout.addWidget(self.next_button)

        self.layout.addLayout(self.navigation_layout)

        self.calendar_layout = QGridLayout()
        self.layout.addLayout(self.calendar_layout)

        self.dates = {}
        self.current_date = QDate.currentDate()
        self.initUI()
        self.setDate(self.current_date.year(), self.current_date.month())

        self.account_data = {}

    def initUI(self):
        # Create labels for the days of the week
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", 'Sun']
        label_width = int(screen_width * 0.035)
        label_height = int(screen_height * 0.045)
        font_size = 8

        font = QFont()
        font.setPointSize(font_size)
        for i, day in enumerate(days_of_week):
            day_label = QLabel(day)
            day_label.setFixedSize(label_width, label_height)
            day_label.setAlignment(Qt.AlignCenter)
            self.calendar_layout.addWidget(day_label, 0, i)

        # Create labels for each day in the month
        for row in range(1, 7):  # 6 weeks to cover all days in a month
            for col in range(7):
                date_label = QLabel("")
                date_label.setFixedSize(label_width, label_height)
                date_label.setAlignment(Qt.AlignCenter)
                date_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                date_label.setFont(font)
                self.calendar_layout.addWidget(date_label, row, col)
                self.dates[(row, col)] = date_label

    def setDate(self, year, month):
        self.current_month_label.setText(f"{QDate.longMonthName(month)} {year}")
        self.current_month_label.setAlignment(Qt.AlignCenter)
        date = QDate(year, month, 1)
        day_of_week = date.dayOfWeek() - 1  # PyQt5: Monday=1, Sunday=7
        for row in range(1, 7):
            for col in range(7):
                self.dates[(row, col)].setText("")

        row = 1
        col = day_of_week
        while date.month() == month:
            if col < 7:  # Exclude Sunday
                self.dates[(row, col)].setText(str(date.day()))
                col += 1
            date = date.addDays(1)
            if col >= 7:
                col = 0
                row += 1

    def setText(self, day, text):
        for (row, col), label in self.dates.items():
            if label.text() == str(day):
                label.setText(f"{day}\n{text}")
                break

    def update_calendar(self):
        try:
            if self.account_type == 'NinjaTrader':
                time_column_name = 'EntryT'
            elif self.account_type == 'TradingView':
                time_column_name = 'Time'
            data = self.account_data
            data = data.groupby(time_column_name).agg({'Profit': 'sum', 'LorS': 'first'}).reset_index()

            data[time_column_name] = pd.to_datetime(data[time_column_name])
            data['Date'] = data[time_column_name].dt.date
            grouped_data = data.groupby('Date').agg({
                'Profit': 'sum',
                time_column_name: 'count'  # Count the number of trades (using any column, here EntryT)
            }).rename(columns={time_column_name: 'Trades'}).reset_index()

            # Add text to the calendar based on the grouped data
            for index, row in grouped_data.iterrows():
                date = row['Date']
                if date.month == self.current_date.month() and date.year == self.current_date.year():
                    day = date.day
                    text = f"Profit: {row['Profit']}\nTrades: {row['Trades']}"
                    self.setText(day, text)
        except Exception as e:
            print(f'Failed to update calendar: {e}')

    def prevMonth(self):
        self.current_date = self.current_date.addMonths(-1)
        self.setDate(self.current_date.year(), self.current_date.month())
        self.update_calendar()

    def nextMonth(self):
        self.current_date = self.current_date.addMonths(1)
        self.setDate(self.current_date.year(), self.current_date.month())
        self.update_calendar()