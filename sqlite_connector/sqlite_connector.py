import sqlite3 as sq

import pandas as pd


class SQLiteConnector:
    """Manage database."""

    def __init__(self):
        self.conn = sq.connect('db.db')
        self.cursor = self.conn.cursor()

        # create tables if they don't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
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

        # TODO profile data

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def insert_into_assets(self, data, name):
        # transform dataframe into suitable form
        data.reset_index(inplace=True)
        data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
        data.fillna({'Dividends': 0, 'Stock Splits': 0}, inplace=True)
        data['Name'] = [name] * len(data)
        values = [tuple(row) for row in data.itertuples(index=False, name=None)]

        # execute query
        self.cursor.executemany("""INSERT INTO assets
                                (date, open, high, low, close, volume, dividends, stock_splits, name)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
        self.conn.commit()

    def get_data_if_exists(self, asset_abbr):
        self.cursor.execute(f"SELECT * FROM assets WHERE name='{asset_abbr}'")
        data = self.cursor.fetchall()
        data = pd.DataFrame(data, columns=(
        'ID', 'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'))
        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')
        data.set_index('Date', inplace=True)
        return data


sqlite = SQLiteConnector()