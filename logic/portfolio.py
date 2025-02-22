import numpy as np
import pandas as pd

from logic.asset import Asset

import datetime as dt


class Portfolio:
    """Simulated portfolio."""

    def __init__(self):
        self.static_assets = {}
        self.periodic_assets = {}

    def add_asset(self, name: str, shares: float) -> None:
        asset = Asset(name)
        if self.static_assets.get(asset, None):
            self.static_assets[asset] += shares
            return
        self.static_assets[asset] = shares

    def add_periodic_asset(self, asset, period, shares) -> None:
        self.periodic_assets[asset] = [period, shares]

    def get_periodic_asset(self, asset) -> list[int, float]:
        return self.periodic_assets.get(asset, [0, 0])

    def remove_periodic_asset(self, asset):
        if asset in self.periodic_assets:
            del self.periodic_assets[asset]

    def get_assets(self):
        return list(self.static_assets.keys())

    def remove_asset(self, asset: Asset) -> None:
        if asset in self.static_assets:
            del self.static_assets[asset]

    def get_asset_names(self):
        return list(map(str, self.static_assets))

    def get_shares(self):
        return list(self.static_assets.values())

    def get_pairs(self):
        return self.static_assets.items()

    @property
    def initial_value(self):
        value = 0
        for asset in self.get_assets():
            value += self.static_assets[asset] * asset.history.iloc[-1]['Close']
        return value

    def calc_overlap(self) -> float:
        """Calculate the overlap between the assets in the portfolio."""
        pass

    def test_with_historical_data(self, begin_date: dt.datetime, end_date: dt.datetime) -> tuple[float, float]:
        """Calculate results from historical analysis."""
        # get data for specific period
        buying_price = 0
        final_price = 0

        for asset, shares in self.get_pairs():
            data = asset.get_data_between_dates(begin_date, end_date)
            buying_price += data.iloc[0]['Open'] * shares
            final_price += data.iloc[-1]['Close'] * shares

            # calculate profit from periodic buying
            if asset in self.periodic_assets:
                periodic_res = self.calc_periodic(asset, begin_date, end_date, data)
                buying_price += periodic_res[0]
                final_price += periodic_res[1]

        return buying_price, final_price

    def calc_periodic(self, asset: Asset,
                      begin_date: dt.datetime,
                      end_date: dt.datetime,
                      data: pd.DataFrame) -> tuple[float, float]:
        """Calculate results from periodically bought assets."""
        buying_price = 0
        final_price = 0

        if begin_date < data.index[0]:
            begin_date = data.index[0]

        if end_date > data.index[-1]:
            end_date = data.index[-1]

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

    def test_with_monte_carlo(self, period: int, number_of_simulations: int):
        data = pd.DataFrame()
        initial_portfolio_value = 0
        for asset in self.get_assets():
            data[asset.asset_abbr] = asset.history['Close'] * self.static_assets[asset]
            initial_portfolio_value += self.static_assets[asset] * asset.history.iloc[-1]['Close']

        data = data.dropna()
        returns = np.log(data / data.shift(1))
        shares = self.get_shares()
        total_shares = sum(shares)
        weights = np.array(list(map(lambda s: s / total_shares, shares)))

        # calculate portfolio expected return and volatility
        mu = returns.mean() * period  # annualized returns
        cov_matrix = returns.cov() * period  # annualized covariance matrix

        # portfolio drift (mean return)
        portfolio_return = np.sum(weights * mu)

        # portfolio volatility (standard deviation)
        volatility = np.sqrt(weights.T @ cov_matrix @ weights)

        # generate random shocks from a normal distribution
        rand = np.random.normal(0, 1, (period, number_of_simulations))

        # simulate portfolio price paths
        paths = np.zeros((period, number_of_simulations))
        paths[0] = initial_portfolio_value

        for t in range(1, period):
            paths[t] = (paths[t - 1] * np.exp((portfolio_return - 0.5 * volatility ** 2) /
                                              period + volatility * np.sqrt(1 / period) * rand[t]))

        final_values = paths[-1, :]

        results = {
            'mean': final_values.mean(),
            'worst_case': np.percentile(final_values, 5),
            'best_case': np.percentile(final_values, 95),
            'std_dev': np.std(final_values),
            'risk': (np.sum(final_values < self.initial_value) / len(final_values)) * 100
        }

        return paths, results
