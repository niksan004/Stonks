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
