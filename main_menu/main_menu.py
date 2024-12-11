from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow

from stock_details_window.stock_details_window import AssetDetailsWindow

from config.config import config


class MainMenu(QMainWindow):
    """Display window with menu to navigate app. First interaction with user."""

    def __init__(self):
        super().__init__()

        # windows
        self.stock_window = None

        # set up window
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Stonks')

        # set up menu
        self.menu_bar = None
        self.create_menu()

    def create_menu(self):
        """Manage menu."""

        # set up menu bar
        self.menu_bar = self.menuBar()

        # stock window
        stock_menu_item = QAction('Asset Details', self)
        stock_menu_item.triggered.connect(self.open_asset_window)
        self.menu_bar.addAction(stock_menu_item)

    def open_asset_window(self):
        self.stock_window = AssetDetailsWindow()
        self.stock_window.show()
        self.hide()
