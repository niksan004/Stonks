import unittest
import pandas as pd
import datetime as dt
from unittest.mock import MagicMock
from project.portfolio import Portfolio


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.portfolio = Portfolio()
        self.mock_asset = MagicMock()
        self.mock_asset.name = "AAPL"
        self.mock_asset.history = pd.DataFrame({
            'Close': [150, 155, 160],
            'Open': [145, 150, 152]
        }, index=pd.date_range(start='2024-01-01', periods=3))

        self.mock_asset.get_data_between_dates = MagicMock(return_value=self.mock_asset.history)
        self.mock_asset.asset_abbr = "AAPL"

    def test_remove_asset(self):
        self.portfolio.add_asset("AAPL", 10)
        self.portfolio.remove_asset("AAPL")
        self.assertNotIn(self.mock_asset, self.portfolio.static_assets)

    def test_add_periodic_asset(self):
        self.portfolio.add_periodic_asset(self.mock_asset, 30, 5)
        self.assertIn(self.mock_asset, self.portfolio.periodic_assets)

    def test_remove_periodic_asset(self):
        self.portfolio.add_periodic_asset(self.mock_asset, 30, 5)
        self.portfolio.remove_periodic_asset(self.mock_asset)
        self.assertNotIn(self.mock_asset, self.portfolio.periodic_assets)

    def test_initial_value(self):
        self.portfolio.static_assets[self.mock_asset] = 10
        self.assertEqual(self.portfolio.initial_value, 10 * 160)

    def test_test_with_historical_data(self):
        self.portfolio.static_assets[self.mock_asset] = 10
        begin_date = dt.datetime(2024, 1, 1)
        end_date = dt.datetime(2024, 1, 3)
        buying_price, final_price = self.portfolio.test_with_historical_data(begin_date, end_date)
        self.assertEqual(buying_price, 1450)
        self.assertEqual(final_price, 1600)

if __name__ == '__main__':
    unittest.main()