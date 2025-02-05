from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

import yfinance as yf

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

class PortfolioWindow(Window):
    """Create window with simulated portfolio."""

    def __init__(self):
        super().__init__()

        # set window attributes
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Portfolio')

        # create central widget
        central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)