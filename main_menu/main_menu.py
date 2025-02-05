from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow

from asset_details_window.asset_details_window import AssetDetailsWindow
from portfolio.portfolio import PortfolioWindow
from config.config import config
from navigation.navigation import Window, nav


class MainMenu(Window):
    """Display window with menu to navigate app. First interaction with user."""

    WINDOWS = {
        'Asset Details': AssetDetailsWindow,
        'Portfolio': PortfolioWindow,
    }

    def __init__(self):
        super().__init__()

        # windows
        self.working_windows = []

        # set up window
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Stonks')

        # set up menu
        self.menu_bar = None
        self.create_menu()

        # add main menu to navigation
        # nav.add_window(self)

    def create_menu(self):
        """Manage menu."""

        # set up menu bar
        self.menu_bar = self.menuBar()

        # add menu options
        for window_name in self.WINDOWS:
            menu_item = QAction(window_name, self)
            menu_item.triggered.connect(lambda s, w=self.WINDOWS[window_name]: self.open_window(w))
            self.menu_bar.addAction(menu_item)

    def open_window(self, window_obj):
        window = window_obj()
        window.show()
        self.hide()
