from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QMainWindow,
                               QStackedWidget, QWidget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AniGit")

        root = QWidget()
        layout = QHBoxLayout(root)
        self.setCentralWidget(root)
