from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow


class Navigation:
    """Save windows for navigation back and forth."""

    windows = []
    at = -1

    def add_window(self, window) -> None:
        """Add window and remove old ones forward from current."""
        if self.at < len(self.windows) - 1:
            self.remove_windows(self.at)

        self.windows.append(window)
        self.at += 1

    def remove_windows(self, from_idx) -> None:
        """Remove old windows forward from current."""
        for idx in range(from_idx + 1, len(self.windows)):
            del self.windows[idx]

    def has_forward(self) -> bool:
        return bool(len(self.windows) - self.at - 1)

    def has_back(self) -> bool:
        return self.at > 0

    def move_back(self) -> None:
        self.windows[self.at].hide()
        self.at -= 1
        self.windows[self.at].show()
        self.check_forward_and_back()

    def move_forward(self) -> None:
        self.windows[self.at].hide()
        self.at += 1
        self.windows[self.at].show()
        self.check_forward_and_back()

    def check_forward_and_back(self) -> None:
        """Check if there are windows forward and back."""
        window = self.windows[self.at]
        if not self.has_back():
            window.back.setEnabled(False)
        if self.has_back():
            window.back.setEnabled(True)
        if not self.has_forward():
            window.forward.setEnabled(False)
        if self.has_forward():
            window.forward.setEnabled(True)


nav = Navigation()


class Window(QMainWindow):
    """Modify QMainWindow so it is added to navigation."""

    def __init__(self):
        super().__init__()

        nav.add_window(self)

        self.navigation = self.menuBar()

        self.back = QAction('<-', self)
        self.forward = QAction('->', self)
        nav.check_forward_and_back()

        self.back.triggered.connect(nav.move_back)
        self.navigation.addAction(self.back)

        self.forward.triggered.connect(nav.move_forward)
        self.navigation.addAction(self.forward)
