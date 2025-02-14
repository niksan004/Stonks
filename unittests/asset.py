import unittest
from unittest.mock import Mock, patch
import datetime as dt
import pandas as pd

from project.asset import Asset


class TestAsset(unittest.TestCase):

    def setUp(self):
        """Set up a mock database and Yahoo Finance response."""
        self.mock_sqlite = Mock()
        self.mock_yf = Mock()

        # Mock existing data in database
        self.mock_sqlite.get_data_if_exists.return_value = (
            pd.DataFrame({'close': [100, 102, 105]}, index=pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])),
            'Mock Company'
        )

        # Mock Yahoo Finance Ticker object
        self.mock_yf.Ticker.return_value.history.return_value = pd.DataFrame({'close': [100, 102, 105]})
        self.mock_yf.Ticker.return_value.info = {'shortName': 'Mock Company'}

    def test_get_data_between_dates(self):
        """Test get_data_between_dates returns correct date range."""
        asset = Asset('AAPL')

        start_date = dt.datetime(2024, 1, 2)
        end_date = dt.datetime(2024, 1, 3)

        data = asset.get_data_between_dates(start_date, end_date)

        # Check correct filtering
        self.assertEqual(len(data), 2)
        self.assertEqual(data.index.tolist(), [pd.Timestamp('2024-01-02'), pd.Timestamp('2024-01-03')])


if __name__ == '__main__':
    unittest.main()
