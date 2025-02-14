import pandas as pd


def calc_window_size(app):
    """Calculate window size and return a list [x, y, width, height]."""
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()

    center_x = screen_width // 4
    center_y = screen_height // 4
    window_width = screen_width // 2
    window_height = screen_height // 2

    return tuple([center_x, center_y, window_width, window_height])

def transform_dataframe_for_storage(dataframe: pd.DataFrame, abbrev: str) -> pd.DataFrame:
    dataframe.reset_index(inplace=True)
    dataframe['Date'] = dataframe['Date'].dt.strftime('%Y-%m-%d')
    dataframe.fillna({'Dividends': 0, 'Stock Splits': 0}, inplace=True)
    dataframe['Name'] = [abbrev] * len(dataframe)
    dataframe = dataframe.rename(columns={'Stock Splits': 'Stock_Splits'})
    return dataframe

def transform_dataframe_for_usage(dataframe: list) -> pd.DataFrame:
    dataframe = pd.DataFrame(dataframe, columns=(
        'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'))
    dataframe['Date'] = pd.to_datetime(dataframe['Date'], format='%Y-%m-%d')
    dataframe.set_index('Date', inplace=True)
    return dataframe