import sys

from new_main_window import NewMainWindow
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    window = NewMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
