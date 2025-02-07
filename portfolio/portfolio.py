from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea, \
    QSizePolicy, QHBoxLayout

import yfinance as yf

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from config.config import config
from navigation.navigation import Window


class Asset:
    """Represent an asset."""

    def __init__(self, asset_abbr):
        self.asset_abbr = asset_abbr

        self.asset = yf.Ticker(self.asset_abbr)

        self.asset_name = self.asset.info.get('shortName', None)
        if not self.asset_name:
            raise Exception('No such asset.')

class Portfolio:
    """Simulated portfolio."""

    def __init__(self, assets):
        self.assets = []

class PortfolioChart(QWidget):
    """Pie chart for portfolio."""

    def __init__(self):
        super().__init__()

        self.setMaximumSize(self.geometry().width() - 200, self.geometry().height() - 200)

        # create the matplotlib figure and canvas
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)

        # create a layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Data for the pie chart
        labels = ['AAPL', 'TSLA', 'VWCE', 'Gold']
        sizes = [30, 25, 25, 20]

        # Create pie chart
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'color': 'white'})
        self.figure.set_facecolor(self.palette().color(self.backgroundRole()).name())

        # Display the chart
        self.ax.set_title('Simulated Portfolio', color='gray')
        self.canvas.draw()

class PortfolioWindow(Window):
    """Create window with simulated portfolio."""

    def __init__(self):
        super().__init__()

        # set window attributes
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Portfolio')

        # create central widget
        central_widget = QScrollArea()
        central_widget.setWidgetResizable(True)
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # add search
        self.textbox = None
        self.button = None
        self.table = None
        self.add_search_widgets()
        # self.add_to_table()

        # plot pie chart
        self.plot = PortfolioChart()
        self.asset_layout = QHBoxLayout()
        self.main_layout.addLayout(self.asset_layout)
        self.asset_layout.addWidget(self.plot)

    def add_search_widgets(self):
        """Create and add textbox and button for searches."""
        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText('Enter asset abbreviation')

        self.button = QPushButton('Search')
        self.button.clicked.connect(self.add_to_table)  # will add the chart if search is successful

        self.main_layout.addWidget(self.textbox)
        self.main_layout.addWidget(self.button)

    def add_to_table(self):
        self.table = QTableWidget(self)

        # Set the number of rows and columns
        self.table.setRowCount(5)  # 5 rows
        self.table.setColumnCount(3)  # 3 columns

        # Set the headers (optional)
        self.table.setHorizontalHeaderLabels(["Name", "Age", "City"])

        # Add data to the table (add items by row and column)
        data = [
            ("Alice", 25, "New York"),
            ("Bob", 30, "Los Angeles"),
            ("Charlie", 35, "Chicago"),
            ("David", 40, "Houston"),
            ("Eve", 22, "Phoenix")
        ]

        for row, (name, age, city) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(age)))  # Convert age to string
            self.table.setItem(row, 2, QTableWidgetItem(city))

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.asset_layout.addWidget(self.table)
