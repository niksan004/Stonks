import sys

from PyQt6.QtWidgets import QApplication

from main_menu.main_menu import MainMenu
from config.config import config
from utils.utils import calc_window_size


def main():
   """Enter program."""
   app = QApplication(sys.argv)

   # set window size in config
   config['WINDOW_SIZE'] = calc_window_size(app)

   try:
      # create main menu
      main_menu = MainMenu()
      main_menu.show()
   except Exception as e:
      print(e)

   # run the application event loop
   sys.exit(app.exec())


if __name__ == "__main__":
   main()
