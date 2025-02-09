from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea, \
    QHBoxLayout, QHeaderView, QSizePolicy

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

    def __str__(self):
        return self.asset_name

    def __hash__(self):
        return hash(self.asset_name)

    def __eq__(self, other):
        return self.asset_name == other.asset_name

    @property
    def info(self):
        return self.asset.info


class Portfolio:
    """Simulated portfolio."""

    def __init__(self):
        self.assets = {}

    def add_asset(self, asset_name, shares) -> None:
        asset = Asset(asset_name)
        if self.assets.get(asset, None):
            self.assets[asset] += shares
            return
        self.assets[asset] = shares

    def remove_asset(self, asset: Asset) -> None:
        del self.assets[asset]

    def get_assets(self):
        return list(map(str, self.assets))

    def get_shares(self):
        return self.assets.values()

    def get_pairs(self):
        return self.assets.items()

    def calc_overlap(self) -> float:
        pass


class PortfolioChart(QWidget):
    """Pie chart for portfolio."""

    def __init__(self, portfolio: Portfolio):
        super().__init__()

        self.portfolio = portfolio

        self.setMaximumSize(self.geometry().width() - 200, self.geometry().height() - 200)

        # create the matplotlib figure and canvas
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # create a layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.draw_chart()

    def draw_chart(self) -> None:
        # create pie chart
        self.ax.pie(
            self.portfolio.get_shares(),
            labels=self.portfolio.get_assets(),
            autopct='%1.1f%%', startangle=140,
            textprops={'color': 'white'}
        )
        self.figure.set_facecolor(self.palette().color(self.backgroundRole()).name())

        self.ax.set_title('Simulated Portfolio', color='gray')
        self.canvas.draw()

    def redraw(self, portfolio: Portfolio) -> None:
        self.portfolio = portfolio
        self.ax.clear()
        self.draw_chart()


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

        self.portfolio = Portfolio()

        # declare attributes that could be initialized in other methods
        self.textbox_name = None
        self.textbox_percentage = None
        self.button = None
        self.table = None

        # add search
        self.add_search_widgets()

        # plot pie chart
        self.chart = PortfolioChart(self.portfolio)
        self.table = QTableWidget()
        self.asset_layout = QHBoxLayout()
        self.asset_layout.addWidget(self.chart) # only to look better
        self.asset_layout.addWidget(self.table) # same as ^
        self.main_layout.addLayout(self.asset_layout)

    def add_search_widgets(self):
        """Create and add textbox and button for searches."""
        self.textbox_name = QLineEdit()
        self.textbox_name.setPlaceholderText('Enter asset abbreviation')

        self.textbox_percentage = QLineEdit()
        self.textbox_percentage.setPlaceholderText('Enter shares')

        self.button = QPushButton('Add')
        self.button.clicked.connect(self.add_to_portfolio)  # will add the chart if search is successful

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.textbox_name)
        search_layout.addWidget(self.textbox_percentage)
        search_layout.addWidget(self.button)
        self.main_layout.addLayout(search_layout)

    def add_to_portfolio(self):
        """Add asset to portfolio if it is found."""
        # if an unexpected error occurs
        try:
            self.portfolio.add_asset(self.textbox_name.text(), float(self.textbox_percentage.text()))
        except Exception:
            self.textbox_name.clear()
            self.textbox_percentage.clear()
            self.textbox_name.setPlaceholderText('Error')
            self.textbox_percentage.setPlaceholderText('Error')
            return

        self.reload_chart()
        self.reload_table()

    def reload_table(self):
        # remove old table
        self.asset_layout.removeWidget(self.table)
        self.table = QTableWidget()

        # make table fill empty space
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # remake table with new data
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Asset', 'Shares', ''])

        self.table.setRowCount(len(self.portfolio.get_assets()))
        for row, asset in enumerate(self.portfolio.get_pairs()):
            self.table.setItem(row, 0, QTableWidgetItem(str(asset[0])))
            self.table.setItem(row, 1, QTableWidgetItem(str(asset[1])))

            remove_button = QPushButton('Remove')
            remove_button.clicked.connect(lambda signal, asset_to_remove=asset[0]:
                                          self.remove_from_portfolio(asset_to_remove))
            self.table.setCellWidget(row, 2, remove_button)

        self.asset_layout.addWidget(self.table)

    def reload_chart(self):
        self.chart.redraw(self.portfolio)

    def remove_from_portfolio(self, asset):
        self.portfolio.remove_asset(asset)
        self.reload_table()
        self.reload_chart()
