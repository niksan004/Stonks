import sqlite3 as sq

from logic.utils import transform_dataframe_for_storage, transform_dataframe_for_usage

import pandas as pd


class SQLiteConnector:
    """Manage database."""

    def __init__(self):
        self.conn = sq.connect('db.db')
        # self.cursor = self.conn.cursor()

        # # create tables if they don't exist
        # self.cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS historical (
        #         id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        #         name TEXT NOT NULL,
        #         date TEXT NOT NULL,
        #         open REAL DEFAULT 0,
        #         high REAL DEFAULT 0,
        #         low REAL DEFAULT 0,
        #         close REAL DEFAULT 0,
        #         volume INTEGER DEFAULT 0,
        #         dividends REAL DEFAULT 0,
        #         stock_splits REAL DEFAULT 0
        #     )
        # """)
        #
        # self.cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS assets (
        #         id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        #         abbreviation TEXT NOT NULL,
        #         short_name TEXT
        #     )
        # """)

        # TODO profile data

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def insert_into_db(self, asset_abbrev: str, history: pd.DataFrame) -> None:
        history.to_sql(asset_abbrev, self.conn, if_exists='replace')
        self.conn.commit()

    def get_data_if_exists(self, asset_abbrev: str) -> pd.DataFrame:
        try:
            history = pd.read_sql(f'SELECT * FROM {asset_abbrev}', self.conn, parse_dates=('Date',), index_col='Date', utc=True)
            # history = history.index.dt.normalize()
        except Exception:
            history = pd.DataFrame()
        return history

    # def insert_into_db(self, abbrev, history, info):
    #     # insert historical data
    #     # transform dataframe into suitable form
    #     history = transform_dataframe_for_storage(history, abbrev)
    #     values = [(row.Date,
    #                row.Name,
    #                row.Open,
    #                row.High,
    #                row.Low,
    #                row.Close,
    #                row.Volume,
    #                row.Dividends,
    #                row.Stock_Splits) for row in history.itertuples(index=False)]
    #
    #     self.cursor.executemany("""
    #         INSERT INTO historical
    #         (date, name, open, high, low, close, volume, dividends, stock_splits)
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #     """, values)
    #
    #     # insert asset info
    #     # values = tuple(info.itertuples(index=False, name=None))
    #     # print(type(info.itertuples(index=False, name=None)))
    #     self.cursor.execute(f"""INSERT INTO assets (abbreviation, short_name) VALUES ('{abbrev}', '{info}')""")
    #
    #     self.conn.commit()
    #
    # def get_data_if_exists(self, asset_abbr):
    #     # get data from sqlite
    #     self.cursor.execute(f"""
    #         SELECT name, date, open, high, low, close, volume, dividends, stock_splits
    #         FROM historical
    #         WHERE name=?
    #     """, (asset_abbr,))
    #     history = self.cursor.fetchall()
    #
    #     # transform data to be suitable
    #     history = transform_dataframe_for_usage(history)
    #
    #     self.cursor.execute(f"""SELECT short_name FROM assets WHERE abbreviation='{asset_abbr}'""")
    #
    #     info = self.cursor.fetchone()
    #     if info:
    #         info = info[0]
    #
    #     return [history, info]


sqlite = SQLiteConnector()
