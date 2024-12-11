from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QRadioButton, QButtonGroup, QLineEdit, QPushButton, \
    QHBoxLayout

import yfinance as yf

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from config.config import config


class ChartWindow(QWidget):
    """Create widget with a chart of a ."""

    def __init__(self, asset_abbr):
        super().__init__()

        self.asset_name = ''
        self.asset_abbr = asset_abbr

        # create the matplotlib figure and canvas
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)

        # create a layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # fetch asset data and plot
        self.plot_asset_data()

    def __str__(self):
        return self.asset_name

    def plot_asset_data(self, period='max'):
        asset = yf.Ticker(self.asset_abbr)
        data = asset.history(period)
        
        # raise exception is search is unsuccessful
        if data.empty:
            raise Exception('No data found.')

        self.asset_name = asset.info.get('shortName', 'No company name available')

        # clear the previous plot and plot the new data
        self.ax.clear()

        # create plot
        self.ax.plot(data.index, data['Close'], label=f'{self.asset_name} Close Price', color='blue')
        self.ax.set_title(f'{self.asset_name} Asset Price')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Price (USD)')
        self.ax.legend()
        self.ax.tick_params(axis='x', rotation=45)

        # draw plot
        self.canvas.draw()

    def refresh_with_new_period(self, period):
        self.plot_asset_data(period)


class AssetDetailsWindow(QMainWindow):
    """Create window with the plot widget."""

    def __init__(self):
        super().__init__()

        # set window attributes
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle(f'Asset Search')

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
            self.plot = ChartWindow(self.textbox.text().upper())
        except Exception:
            self.textbox.clear()
            self.textbox.setPlaceholderText('No asset found')
            return

        # add chart to window
        self.main_layout.addWidget(self.plot)

        # create buttons with periods of time for viewing the asset
        self.generate_time_period_buttons()

    def generate_time_period_buttons(self):
        """Add radio buttons for time period."""
        # create radio buttons
        radio_button_1 = QRadioButton("1 month")
        radio_button_2 = QRadioButton("1 year")
        radio_button_3 = QRadioButton("Max")

        # add radio buttons to the button layout
        self.layout_period_buttons = QHBoxLayout()
        self.layout_period_buttons.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.layout_period_buttons.addWidget(radio_button_1)
        self.layout_period_buttons.addWidget(radio_button_2)
        self.layout_period_buttons.addWidget(radio_button_3)

        # add buttons to the main layout
        self.main_layout.addLayout(self.layout_period_buttons)

        # create a QButtonGroup to group the radio buttons together
        self.button_group = QButtonGroup()
        self.button_group.addButton(radio_button_1)
        self.button_group.addButton(radio_button_2)
        self.button_group.addButton(radio_button_3)

        # connect the radio buttons to a method that refreshes the window with new info
        radio_button_1.toggled.connect(lambda: self.plot.refresh_with_new_period('1mo'))
        radio_button_2.toggled.connect(lambda: self.plot.refresh_with_new_period('1y'))
        radio_button_3.toggled.connect(lambda: self.plot.refresh_with_new_period('max'))

    def remove_time_period_buttons(self):
        """Remove radio buttons for time period."""
        self.main_layout.removeItem(self.layout_period_buttons)
        self.button_group = None
        self.layout_period_buttons = None
