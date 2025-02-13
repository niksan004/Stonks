import sqlite3 as sq

import pandas as pd


class SQLiteConnector:
    """Manage database."""

    def __init__(self):
        self.conn = sq.connect('db.db')
        self.cursor = self.conn.cursor()

        # create tables if they don't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL DEFAULT 0,
                high REAL DEFAULT 0,
                low REAL DEFAULT 0,
                close REAL DEFAULT 0,
                volume INTEGER DEFAULT 0,
                dividends REAL DEFAULT 0,
                stock_splits REAL DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                abbreviation TEXT NOT NULL,
                short_name TEXT
            )
        """)

        # TODO profile data

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def insert_into_db(self, abbrev, history, info):
        # insert historical data
        # transform dataframe into suitable form

        history.reset_index(inplace=True)
        history['Date'] = history['Date'].dt.strftime('%Y-%m-%d')
        history.fillna({'Dividends': 0, 'Stock Splits': 0}, inplace=True)
        history['Name'] = [abbrev] * len(history)
        history = history.rename(columns={'Stock Splits': 'Stock_Splits'})
        values = [(row.Date,
                   row.Name,
                   row.Open,
                   row.High,
                   row.Low,
                   row.Close,
                   row.Volume,
                   row.Dividends,
                   row.Stock_Splits) for row in history.itertuples(index=False)]

        self.cursor.executemany("""
            INSERT INTO historical
            (date, name, open, high, low, close, volume, dividends, stock_splits)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

        # insert asset info
        # values = tuple(info.itertuples(index=False, name=None))
        # print(type(info.itertuples(index=False, name=None)))
        self.cursor.execute(f"""INSERT INTO assets (abbreviation, short_name) VALUES ('{abbrev}', '{info}')""")

        self.conn.commit()

    def get_data_if_exists(self, asset_abbr):
        # get data from sqlite
        self.cursor.execute(f"""
            SELECT name, date, open, high, low, close, volume, dividends, stock_splits
            FROM historical 
            WHERE name='{asset_abbr}'
        """)
        history = self.cursor.fetchall()

        # transform data to be suitable
        history = pd.DataFrame(history, columns=(
        'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'))
        history['Date'] = pd.to_datetime(history['Date'], format='%Y-%m-%d')
        history.set_index('Date', inplace=True)

        self.cursor.execute(f"""SELECT short_name FROM assets WHERE abbreviation='{asset_abbr}'""")

        info = self.cursor.fetchone()
        if info:
            info = info[0]

        return [history, info]


sqlite = SQLiteConnector()
