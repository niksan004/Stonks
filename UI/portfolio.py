import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QHeaderView, QGroupBox, QTextEdit, QDialog, QLabel, QScrollArea)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from numpy import ndarray

from logic.config import config
from logic.navigation import Window
from logic.asset import Asset
from logic.portfolio import Portfolio


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
            labels=self.portfolio.get_asset_names(),
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
        central_widget = QWidget()
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

        # add testing with historical data
        self.textbox_begin_date = None
        self.textbox_end_date = None
        self.results_area = None
        self.periodic_assets = {}
        self.add_historical_testing_widgets()

        # add testing with monte carlo
        self.textbox_period = None
        self.textbox_simulations = None
        self.add_monte_carlo_widgets()

        self.show()

    def add_search_widgets(self):
        """Create and add textbox and button for searches."""
        self.textbox_name = QLineEdit('AAPL')
        self.textbox_name.setPlaceholderText('Enter asset abbreviation')

        self.textbox_percentage = QLineEdit('2')
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Asset', 'Shares', '', ''])

        self.table.setRowCount(len(self.portfolio.get_asset_names()))

        for row, asset in enumerate(self.portfolio.get_pairs()):
            # asset is tuple (asset, shares)
            # asset column
            self.table.setItem(row, 0, QTableWidgetItem(str(asset[0])))

            # shares column
            self.table.setItem(row, 1, QTableWidgetItem(str(asset[1])))

            # add periodically column
            add_periodically_button = QPushButton('Set Periodical Buying')
            add_periodically_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            add_periodically_button.clicked.connect(lambda signal, asset_to_add=asset[0]:
                                                    self.add_periodically_menu(asset_to_add))
            self.table.setCellWidget(row, 2, add_periodically_button)

            # remove column (doesn't have a column name)
            remove_button = QPushButton('Remove')
            remove_button.clicked.connect(lambda signal, asset_to_remove=asset[0]:
                                          self.remove_from_portfolio(asset_to_remove))
            self.table.setCellWidget(row, 3, remove_button)

        self.asset_layout.addWidget(self.table)

    def reload_chart(self):
        self.chart.redraw(self.portfolio)

    def remove_from_portfolio(self, asset: Asset):
        """Remove asset from portfolio and table."""
        self.portfolio.remove_asset(asset)
        self.reload_table()
        self.reload_chart()

    def add_periodically_menu(self, asset: Asset):
        """Add periodic buying of asset."""
        result = self.portfolio.get_periodic_asset(asset) # result will be [<period>, <shares-to-buy>]
        dialog = PeriodDialog(result)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if result == [0, 0]:
                self.portfolio.remove_periodic_asset(asset)
                return
            self.portfolio.add_periodic_asset(asset, result[0], result[1])

    def add_historical_testing_widgets(self):
        testing_area = QGroupBox('Historical Testing Area')
        layout = QHBoxLayout()

        self.textbox_begin_date = QLineEdit('2016-01-01')
        self.textbox_begin_date.setPlaceholderText('Starting Date (YYYY-MM-DD)')
        layout.addWidget(self.textbox_begin_date)

        self.textbox_end_date = QLineEdit('2025-01-01')
        self.textbox_end_date.setPlaceholderText('End Date (YYYY-MM-DD)')
        layout.addWidget(self.textbox_end_date)

        button = QPushButton('Historical Data')
        button.clicked.connect(self.test_with_historical_data)
        layout.addWidget(button)

        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)

        outer_layout = QVBoxLayout()
        outer_layout.addLayout(layout)
        outer_layout.addWidget(self.results_area)
        testing_area.setLayout(outer_layout)
        self.main_layout.addWidget(testing_area)

    def test_with_historical_data(self) -> None:
        begin_date = pd.to_datetime(self.textbox_begin_date.text())
        end_date = pd.to_datetime(self.textbox_end_date.text())

        buying_price, final_price = self.portfolio.test_with_historical_data(begin_date, end_date)
        profit = final_price - buying_price

        self.results_area.setHtml(f"""
            <h2>Historical Data Results</h2>
            <p><big>Buying price: {buying_price: .2f} $</big></p>
            <p><big>Final price: {final_price: .2f} $</big></p>
            <p><big>Profit: {profit: .2f} $</big></p>
            <p><big>Percentage Profit: {profit / buying_price * 100: .2f} %</big></p>
        """)

    def add_monte_carlo_widgets(self):
        testing_area = QGroupBox('Monte Carlo Area')
        layout = QHBoxLayout()

        self.textbox_period = QLineEdit('252')
        self.textbox_period.setPlaceholderText('Enter Period in Trading Days')
        layout.addWidget(self.textbox_period)

        self.textbox_simulations = QLineEdit('1000')
        self.textbox_simulations.setPlaceholderText('Enter Number of Simulations')
        layout.addWidget(self.textbox_simulations)

        calculate_button = QPushButton('Monte Carlo')
        calculate_button.clicked.connect(self.test_with_monte_carlo)
        layout.addWidget(calculate_button)

        testing_area.setLayout(layout)
        self.main_layout.addWidget(testing_area)

    def test_with_monte_carlo(self):
        try:
            period = int(self.textbox_period.text())
            simulations = int(self.textbox_simulations.text())
        except ValueError:
            self.textbox_period.clear()
            self.textbox_period.setPlaceholderText('Invalid input')
            self.textbox_simulations.clear()
            self.textbox_simulations.setPlaceholderText('Invalid input')
            return

        MonteCarloWindow(self.portfolio, period, simulations)
        self.hide()


class PeriodDialog(QDialog):
    """Pop up window to set up periodic buying of assets."""

    def __init__(self, result: list):
        super().__init__()

        self.result = result

        self.setWindowTitle('Select Periodic Buying')

        textbox_layout = QHBoxLayout()

        self.period_textbox = QLineEdit()
        self.period_textbox.setPlaceholderText('Enter period in days')
        textbox_layout.addWidget(self.period_textbox)

        self.shares_textbox = QLineEdit()
        self.shares_textbox.setPlaceholderText('Enter number of shares')
        textbox_layout.addWidget(self.shares_textbox)

        button_layout = QHBoxLayout()

        self.apply_button = QPushButton('Apply')
        self.apply_button.clicked.connect(self.get_input)
        button_layout.addWidget(self.apply_button)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout = QVBoxLayout()

        if self.result:
            already_set_data = QLabel(f'Already set: period={self.result[0]} days shares={self.result[1]}')
            main_layout.addWidget(already_set_data)

        main_layout.addLayout(textbox_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def get_input(self):
        # if incomplete data is entered pressing apply does nothing
        if not self.period_textbox.text() or not self.shares_textbox.text():
            return
        self.result[0] = int(self.period_textbox.text())
        self.result[1] = float(self.shares_textbox.text())
        self.accept()


class MonteCarloChartWidget(QWidget):
    """Create the plot for Monte Carlo simulations."""

    def __init__(self, price_paths: ndarray, name: str):
        super().__init__()
        # create plot
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        self.ax.set_title(f'{name}', color='gray')
        self.ax.set_xlabel('Trading Days', color='gray')
        self.ax.set_ylabel('Price (USD)', color='gray')
        self.ax.tick_params(axis='both', colors='gray')
        bg_color = self.palette().color(self.backgroundRole()).name()
        self.figure.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        self.ax.plot(price_paths, lw=0.5)

        # create a layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.canvas.setFixedHeight(config['WINDOW_SIZE'][3])
        self.canvas.draw()


class MonteCarloWindow(Window):
    """Display information about Monte Carlo simulations."""

    def __init__(self, portfolio: Portfolio, period: int, number_of_simulations: int):
        super().__init__()

        # create central widget
        self.scroll_area = QScrollArea()
        self.main_layout = QVBoxLayout()
        self.central_widget = QWidget()

        # calculate monte carlo and add data to window
        portfolio_paths, stats = portfolio.test_with_monte_carlo(period, number_of_simulations)
        self.main_layout.addWidget(MonteCarloChartWidget(portfolio_paths, 'Whole Portfolio'))
        self.main_layout.addWidget(QLabel(f'Initial Portfolio Value: {portfolio.initial_value:.2f}'))
        self.main_layout.addWidget(QLabel(f'Mean Portfolio Value: {stats['mean']:.2f}'))
        self.main_layout.addWidget(QLabel(f'Worst Case (5th Percentile): {stats['worst_case']:.2f}'))
        self.main_layout.addWidget(QLabel(f'Best Case (95th Percentile): {stats['best_case']:.2f}'))
        self.main_layout.addWidget(QLabel(f'Standard Deviation: {stats['std_dev']:.2f}'))
        self.main_layout.addWidget(QLabel(f'Probability of Loss: {stats['risk']:.2f}%'))

        self.central_widget.setLayout(self.main_layout)

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.central_widget)

        self.setCentralWidget(self.scroll_area)

        # set window attributes
        self.setGeometry(*config['WINDOW_SIZE'])
        self.setWindowTitle('Monte Carlo')
        self.show()
