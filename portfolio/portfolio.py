import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QHeaderView, QGroupBox, QTextEdit, QDialog, QLabel, QScrollArea)

import yfinance as yf

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from numpy import ndarray
from pandas.core.interchange.dataframe_protocol import DataFrame

from config.config import config
from navigation.navigation import Window

from sqlite_connector.sqlite_connector import sqlite

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

    def get_data_between_dates(self, start_date: str, end_date: str):
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        return self.history.loc[(self.history.index >= start_date) & (self.history.index <= end_date)]

    def get_data_in_period(self, period: int):
        """Get data from specific period (ex. last month)."""
        tz = self.history.index.tzinfo
        today = dt.datetime.today()
        delta = today.replace(tzinfo=tz) - dt.timedelta(days=period)

        # filter for period
        return self.history.loc[self.history.index >= delta]


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

    def get_assets(self):
        return self.assets.keys()

    def remove_asset(self, asset: Asset) -> None:
        del self.assets[asset]

    def get_asset_names(self):
        return list(map(str, self.assets))

    def get_shares(self):
        return list(self.assets.values())

    def get_pairs(self):
        return self.assets.items()

    def calc_overlap(self) -> float:
        """Calculate the overlap between the assets in the portfolio."""
        pass

    def test_with_historical_data(self):
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

        # add testing option
        self.textbox_begin_date = None
        self.textbox_end_date = None
        self.results_area = None
        self.periodic_assets = {}
        self.add_testing_widgets()

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

    def remove_from_portfolio(self, asset):
        """Remove asset from portfolio and table."""
        self.portfolio.remove_asset(asset)
        self.reload_table()
        self.reload_chart()

    def add_periodically_menu(self, asset):
        """Add periodic buying of asset."""
        result = self.periodic_assets.get(asset, [0, 0]) # result will be [<period>, <shares-to-buy>]
        dialog = PeriodDialog(result)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.periodic_assets[asset] = result

    def add_testing_widgets(self):
        testing_area = QGroupBox('Testing Area')
        layout = QHBoxLayout()

        self.textbox_begin_date = QLineEdit('2016-01-01')
        self.textbox_begin_date.setPlaceholderText('Starting Date (YYYY-MM-DD)')
        layout.addWidget(self.textbox_begin_date)

        self.textbox_end_date = QLineEdit('2025-01-01')
        self.textbox_end_date.setPlaceholderText('End Date (YYYY-MM-DD)')
        layout.addWidget(self.textbox_end_date)

        button = QPushButton('Calculate Using Historical Data')
        button.clicked.connect(self.test_with_historical_data)
        layout.addWidget(button)

        button_monte_carlo = QPushButton('Monte Carlo')
        button_monte_carlo.clicked.connect(self.test_with_monte_carlo)

        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)

        outer_layout = QVBoxLayout()
        outer_layout.addLayout(layout)
        outer_layout.addWidget(self.results_area)
        outer_layout.addWidget(button_monte_carlo)
        testing_area.setLayout(outer_layout)
        self.main_layout.addWidget(testing_area)

    def test_with_historical_data(self) -> None:
        try:
            # get data for specific period
            buying_price = 0
            final_price = 0
            dividend_profit = 0

            begin_date = self.textbox_begin_date.text()
            end_date = self.textbox_end_date.text()

            for asset, shares in self.portfolio.get_pairs():
                data = asset.get_data_between_dates(begin_date, end_date)
                dividend_profit += sum(data['Dividends'][data['Dividends'] != 0]) * shares
                buying_price += data.iloc[0]['Open'] * shares
                final_price += data.iloc[-1]['Close'] * shares

                # calculate profit from periodic buying
                periodic_res = self.calc_periodic(asset, begin_date, end_date, data)
                buying_price += periodic_res[0]
                final_price += periodic_res[1]

            profit = final_price - buying_price + dividend_profit
            self.results_area.setHtml(f"""
                <h2>Historical Data Results</h2>
                <p><big>Buying price: {round(buying_price, 2)} $</big></p>
                <p><big>Final price: {round(final_price, 2)} $</big></p>
                <p><big>Profit: {round(profit, 2)} $</big></p>
                <p><big>Percentage Profit: {round(profit / buying_price * 100, 2)} %</big></p>
            """)
        except Exception as e:
            print(e)

    def calc_periodic(self, asset: Asset, begin_date: str, end_date: str, data: pd.DataFrame) -> tuple[float, float]:
        buying_price = 0
        final_price = 0
        begin_date = pd.to_datetime(begin_date)
        end_date = pd.to_datetime(end_date)

        if begin_date < data.index[0]:
            begin_date = data.index[0]

        if end_date > data.index[-1]:
            end_date = data.index[-1]

        if asset in self.periodic_assets:
            period = self.periodic_assets[asset][0]
            shares_per_period = self.periodic_assets[asset][1]
            delta = pd.Timedelta(days=period)
            begin_date += delta
            while begin_date <= end_date:
                one_day_delta = pd.Timedelta(days=1)
                temp_date = begin_date
                to_buy = data.loc[data.index == begin_date]['Open']
                while to_buy.empty and temp_date <= end_date:
                    temp_date += one_day_delta
                    to_buy = data.loc[data.index == temp_date]['Open']

                if to_buy.empty:
                    begin_date += delta
                    continue

                buying_price += to_buy.iloc[0] * shares_per_period
                final_price += data.iloc[-1]['Close'] * shares_per_period
                begin_date += delta

        return buying_price, final_price

    def test_with_monte_carlo(self):
        try:
            monte_carlo_window = MonteCarloWindow(self.portfolio)
            self.hide()
        except Exception as e:
            print(e)


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
        self.result[1] = int(self.shares_textbox.text())
        self.accept()

def calculate_monte_carlo_asset(asset: Asset, shares: float) -> ndarray:
    """Make Monte Carlo simulation for a single asset."""
    prices = asset.history['Close'].copy()
    returns = np.log(prices / prices.shift(1))
    sigma = returns.std() * np.sqrt(252)

    # 3. Set simulation parameters
    risk_free_rate = 0.01  # Risk-free rate (assumed 1% per year)
    delta_time = 1 / 252  # Time step (1 trading day)
    trading_days = 252  # Total number of trading days to simulate (1 year)
    simulations = 1000  # Number of simulation paths
    starting_price = prices.iloc[-1] * shares  # Starting price from last available data point

    rand = np.random.normal(0, 1, (trading_days, simulations))

    # 5. Initialize the price paths array
    price_paths = np.zeros((trading_days, simulations))
    price_paths[0] = starting_price * np.exp(
        (risk_free_rate - 0.5 * sigma ** 2) * delta_time + sigma * np.sqrt(delta_time) * rand[0])

    # 6. Simulate the price paths using the formula:
    #    S_{t+dt} = S_t * exp((r - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
    for t in range(1, trading_days):
        price_paths[t] = price_paths[t - 1] * np.exp(
            (risk_free_rate - 0.5 * sigma ** 2) * delta_time + sigma * np.sqrt(delta_time) * rand[t])

    return price_paths


def calculate_monte_carlo_portfolio(portfolio: Portfolio) -> ndarray:
    data = pd.DataFrame()
    initial_portfolio_value = 0
    for asset in list(portfolio.get_assets()):
        data[asset.asset_abbr] = asset.history['Close'] * portfolio.assets[asset]
        initial_portfolio_value += portfolio.assets[asset] * asset.history.iloc[-1]['Close']

    data = data.dropna()
    returns = np.log(data / data.shift(1))
    shares = portfolio.get_shares()
    total_shares = sum(shares)
    weights = np.array(list(map(lambda s: s / total_shares, shares)))

    # Calculate portfolio expected return and volatility
    mu = returns.mean() * 252  # Annualized returns
    cov_matrix = returns.cov() * 252  # Annualized covariance matrix

    # Portfolio drift (mean return)
    portfolio_return = np.sum(weights * mu)

    # Portfolio volatility (standard deviation)
    portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)

    # Monte Carlo Simulation Parameters
    trading_days = 252
    simulations = 1000

    # Generate random shocks (Z) from a normal distribution
    rand = np.random.normal(0, 1, (trading_days, simulations))

    # Simulate portfolio price paths
    portfolio_paths = np.zeros((trading_days, simulations))
    portfolio_paths[0] = initial_portfolio_value

    for t in range(1, trading_days):
        portfolio_paths[t] = portfolio_paths[t - 1] * np.exp(
            (portfolio_return - 0.5 * portfolio_volatility ** 2) / trading_days
            + portfolio_volatility * np.sqrt(1 / trading_days) * rand[t]
        )

    return portfolio_paths

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

    def __init__(self, portfolio: Portfolio):
        super().__init__()

        calculate_monte_carlo_portfolio(portfolio)

        # create central widget
        self.scroll_area = QScrollArea()
        self.main_layout = QVBoxLayout()
        self.central_widget = QWidget()

        # self.charts = []
        # for asset, shares in list(portfolio.get_pairs()):
        #     paths = calculate_monte_carlo_asset(asset, shares)
        #     chart = MonteCarloChartWidget(paths, str(asset))
        #     self.main_layout.addWidget(chart)
        #     self.charts.append(chart)

        portfolio_paths = calculate_monte_carlo_portfolio(portfolio,periodic)
        self.main_layout.addWidget(MonteCarloChartWidget(portfolio_paths, 'Whole Portfolio'))

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
