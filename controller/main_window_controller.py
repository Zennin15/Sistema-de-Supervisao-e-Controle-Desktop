from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem
from ui.main_window import Ui_MainWindow
from controller.limits_configuration_window_controller import LimitConfigurationController

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)   

        self.limites_registrados = []

        self.ui.botaoLimite.clicked.connect(self.abrir_janela)

    # Abre a janela de registro de limites
    def abrir_janela(self):
        popup = LimitConfigurationController(parent = self)

        popup.carregar_dados(self.limites_registrados)

        if popup.exec() == QDialog.Accepted:
           self.limites_registrados = popup.get_dados()
            
            

            