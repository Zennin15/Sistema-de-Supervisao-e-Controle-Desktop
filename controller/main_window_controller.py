from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem
from ui.main_window import Ui_MainWindow

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)   