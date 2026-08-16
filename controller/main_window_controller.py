from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem
from ui.main_window import Ui_MainWindow
from controller.limits_configuration_window_controller import LimitConfigurationController
from controller.dashboard_window_controller import DashboardWindowController

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)   

        self.limites_registrados = []

        self.ui.botaoLimite.clicked.connect(self.abrir_janela)
        self.ui.pushButton_3.clicked.connect(self.abrir_dashboard)

    # Abre a janela de registro de limites
    def abrir_janela(self):
        popup = LimitConfigurationController(parent = self)

        popup.carregar_dados(self.limites_registrados)

        if popup.exec() == QDialog.Accepted:
           self.limites_registrados = popup.get_dados()

    # Abre a tela de Dashboard de telemetria
    def abrir_dashboard(self):
        dashboard = DashboardWindowController(parent=self)
        dashboard.exec()
