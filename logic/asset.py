from logic.sqlite_connector import sqlite

import yfinance as yf

import datetime as dt


class Asset:
    """Represent an asset."""

    def __init__(self, asset_abbr):
        self.abbrev = asset_abbr.upper()
        self.ticker = yf.Ticker(self.abbrev)
        self.history, _ = sqlite.get_data_if_exists(self.abbrev)

        if self.history.empty:
            self.history = self.ticker.history('max')
            self.history = self.history.tz_convert(None)
            sqlite.insert_into_db(self.abbrev, self.history.copy(), self.short_name)

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
        return self.ticker.info.get('shortName', 'No company name available')

    def get_data_between_dates(self, start_date: dt.datetime, end_date: dt.datetime):
        return self.history.loc[(self.history.index >= start_date) & (self.history.index <= end_date)]

    def get_data_in_period(self, period: int):
        """Get data from specific period (ex. last month)."""
        try:
            delta = dt.datetime.today() - dt.timedelta(days=period)
            # filter for period
            return self.history.loc[self.history.index >= delta]
        except Exception as e:
            print(e)
