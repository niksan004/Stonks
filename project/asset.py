from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QButtonGroup, QLineEdit, QPushButton, \
    QHBoxLayout

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from project.config import config
from project.navigation import Window
from project.sqlite_connector import sqlite

import yfinance as yf

import datetime as dt


class Asset:
    """Represent an asset."""

    def __init__(self, asset_abbr):
        self.asset_abbr = asset_abbr.upper()
        self.history, self.info = sqlite.get_data_if_exists(self.asset_abbr)

        if self.history.empty:
            self.asset = yf.Ticker(self.asset_abbr)
            self.history = self.asset.history('max')
            self.info = self.asset.info.get('shortName', 'No company name available')
            sqlite.insert_into_db(self.asset_abbr, self.history.copy(), self.info)

        self.history.index.tz_localize(None)

        # raise exception if search is unsuccessful
        if self.history.empty:
            raise Exception('No data found.')

    def __str__(self):
        return self.short_name

    def __hash__(self):
        return hash(self.short_name)

    def __eq__(self, other):
        return self.short_name == other.short_name

    @property
    def short_name(self):
        return self.info

    def get_data_between_dates(self, start_date: dt.datetime, end_date: dt.datetime):
        return self.history.loc[(self.history.index >= start_date) & (self.history.index <= end_date)]

    def get_data_in_period(self, period: int):
        """Get data from specific period (ex. last month)."""
        tz = self.history.index.tzinfo
        today = dt.datetime.today()
        delta = today.replace(tzinfo=tz) - dt.timedelta(days=period)

        # filter for period
        return self.history.loc[self.history.index >= delta]


class ChartWidget(QWidget):
    """Create widget with a chart of an asset."""

    def __init__(self, asset_abbr):
        super().__init__()

        self.asset = Asset(asset_abbr)

        # create the matplotlib figure and canvas
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)

        # create a layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # fetch asset data and plot
        self.plot_asset_data()

    def plot_asset_data(self):
        """Plot asset chart."""

        # clear the previous plot and plot the new data
        self.ax.clear()

        # create plot
        self.create_plot(self.asset.history)

    def refresh_with_new_period(self, period):
        """Refresh plot with new period."""
        self.ax.clear()
        self.create_plot(self.asset.get_data_in_period(period))

    def create_plot(self, data):
        """Create plot."""
        # create plot
        self.ax.plot(data.index, data['Close'], label=f'{self.asset.short_name} Close Price', color='green')
        self.ax.set_title(f'{self.asset.short_name} Asset Price', color='gray')
        self.ax.set_xlabel('Date', color='gray')
        self.ax.set_ylabel('Price (USD)', color='gray')
        self.ax.legend()
        self.ax.tick_params(axis='both', rotation=15, colors='gray')

        bg_color = self.palette().color(self.backgroundRole()).name()
        self.figure.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        # draw plot
        self.canvas.draw()

class AssetDetailsWindow(Window):
    """Create window with the plot widget."""

    def __init__(self):
        super().__init__()

        # set window attributes
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Asset Search')

        # create central widget
        central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # declare items for later initialization
        self.textbox = None
        self.button = None
        # the ones below will be initialized when user enters asset name
        self.plot = None
        self.button_group = None
        self.layout_period_buttons = None

        self.add_search_widgets()

        self.show()

    def add_search_widgets(self):
        """Create and add textbox and button for searches."""
        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText('Enter asset abbreviation')

        self.button = QPushButton('Search')
        self.button.clicked.connect(self.display_asset) # will add the chart if search is successful

        self.main_layout.addWidget(self.textbox)
        self.main_layout.addWidget(self.button)


    def display_asset(self):
        """Get result from textbox and display asset."""
        # remove old chart and buttons if there was a previous search
        if self.plot:
            self.main_layout.removeWidget(self.plot)
            self.remove_time_period_buttons()

        # if an unexpected error occurs
        try:
            self.plot = ChartWidget(self.textbox.text())
        except Exception as e:
            self.textbox.clear()
            self.textbox.setPlaceholderText('No asset found')
            print(e)
            return

        # add chart to window
        self.main_layout.addWidget(self.plot)

        # create buttons with periods of time for viewing the asset
        self.generate_time_period_buttons()

    def generate_time_period_buttons(self):
        """Add radio buttons for time period."""
        # create radio buttons
        buttons = [QRadioButton(period) for period in config['TIME_PERIODS']]

        # add radio buttons to the button layout
        self.layout_period_buttons = QHBoxLayout()
        self.layout_period_buttons.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for button in buttons:
            self.layout_period_buttons.addWidget(button)

        # add buttons to the project layout
        self.main_layout.addLayout(self.layout_period_buttons)

        # create a QButtonGroup to group the radio buttons together
        self.button_group = QButtonGroup()
        for button in buttons:
            self.button_group.addButton(button)

        # connect the radio buttons to a method that refreshes the window with new info
        for button, period in zip(buttons, config['TIME_PERIODS'].values()):
            button.toggled.connect(lambda conn, p=period: self.plot.refresh_with_new_period(p))

    def remove_time_period_buttons(self):
        """Remove radio buttons for time period."""
        self.main_layout.removeItem(self.layout_period_buttons)
        self.button_group = None
        self.layout_period_buttons = None
