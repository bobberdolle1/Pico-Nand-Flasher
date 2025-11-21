import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt6.QtGui import QFont

# Ensure project root is on sys.path to allow imports like src.* when launched directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Lazy import inside handlers to speed up launcher start


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pico NAND Flasher — Launcher")
        self.setGeometry(100, 100, 400, 220)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("Выберите приложение для запуска")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        self.btn_modern = QPushButton("🚀 Запустить Modern GUI (PyQt6)")
        self.btn_analyzer = QPushButton("🔍 Открыть Dump Analyzer")

        self.btn_modern.clicked.connect(self.open_modern)
        self.btn_analyzer.clicked.connect(self.open_analyzer)

        layout.addWidget(self.btn_modern)
        layout.addWidget(self.btn_analyzer)
        layout.addStretch()

    def open_modern(self):
        from main.gui.GUI_modern import NANDFlasherGUI

        self.child = NANDFlasherGUI()
        self.child.show()

    def open_analyzer(self):
        from main.gui.dump_analyzer import DumpAnalyzer

        self.child2 = DumpAnalyzer()
        self.child2.show()


def main():
    app = QApplication(sys.argv)
    font = QFont("Arial", 9)
    app.setFont(font)

    win = LauncherWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
