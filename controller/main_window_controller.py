from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QPushButton
from PySide6.QtCore import QDateTime
from ui.main_window import Ui_MainWindow
from controller.limits_configuration_window_controller import LimitsConfigurationWindowController
from controller.dashboard_window_controller import DashboardWindowController
from controller.serial_controller import SerialConfigController

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)   

        self.limites_registrados = []

        # Criar botão de fechar histórico dinamicamente acima da tabela
        if hasattr(self.ui, 'tableEventos'):
            self.btn_fechar_historico = QPushButton("Fechar Histórico", self.ui.centralwidget)
            self.btn_fechar_historico.setGeometry(self.ui.tableEventos.x() + self.ui.tableEventos.width() - 130, 
                                                self.ui.tableEventos.y() - 25, 130, 23)
            self.btn_fechar_historico.clicked.connect(self.fechar_historico)
            self.btn_fechar_historico.setVisible(False)
            self.ui.tableEventos.setVisible(False)

        self.configurar_tabela_eventos()

        # Conexões dos botões
        if hasattr(self.ui, 'pushButton_4'):
            self.ui.pushButton_4.clicked.connect(self.abrir_janela)

        if hasattr(self.ui, 'pushButton'):
            self.ui.pushButton.clicked.connect(self.exibir_historico)

        if hasattr(self.ui, 'pushButton_3'):
            self.ui.pushButton_3.clicked.connect(self.abrir_dashboard)

        if hasattr(self.ui, 'pushButton_2'):
            self.ui.pushButton_2.clicked.connect(self.abrir_configuracao_serial)

    def configurar_tabela_eventos(self):
        if hasattr(self.ui, 'tableEventos'):
            self.ui.tableEventos.setColumnCount(3)
            self.ui.tableEventos.setHorizontalHeaderLabels(["Data/Hora", "Tipo de Evento", "Descrição"])
            
            header = self.ui.tableEventos.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)

    def registrar_evento(self, tipo: str, descricao: str):
        if hasattr(self.ui, 'tableEventos'):
            row_position = self.ui.tableEventos.rowCount()
            self.ui.tableEventos.insertRow(row_position)

            data_hora = QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm:ss")

            self.ui.tableEventos.setItem(row_position, 0, QTableWidgetItem(data_hora))
            self.ui.tableEventos.setItem(row_position, 1, QTableWidgetItem(tipo))
            self.ui.tableEventos.setItem(row_position, 2, QTableWidgetItem(descricao))

    def exibir_historico(self):
        """Exibe a tabela e o botão de fechar."""
        if hasattr(self.ui, 'tableEventos'):
            self.ui.tableEventos.setVisible(True)
            if hasattr(self, 'btn_fechar_historico'):
                self.btn_fechar_historico.setVisible(True)

    def fechar_historico(self):
        """Oculta a tabela e o botão de fechar."""
        if hasattr(self.ui, 'tableEventos'):
            self.ui.tableEventos.setVisible(False)
            if hasattr(self, 'btn_fechar_historico'):
                self.btn_fechar_historico.setVisible(False)

    def abrir_janela(self):
        popup = LimitsConfigurationWindowController(parent=self)
        popup.carregar_dados(self.limites_registrados)

        if popup.exec() == QDialog.Accepted:
            self.limites_registrados = popup.get_dados()
            
            for idx, limite in enumerate(self.limites_registrados, start=1):
                tensao = limite.get("Tensao", "-")
                corrente = limite.get("Corrente", "-")
                self.registrar_evento("Configuração", f"Regra #{idx}: Tensão Max={tensao}V, Corrente Max={corrente}A")
            
            QMessageBox.information(self, "Sucesso", "Limites salvos e registrados no histórico!")

    def abrir_dashboard(self):
        dashboard = DashboardWindowController(parent=self)
        dashboard.exec()

    def abrir_configuracao_serial(self):
        dialog = SerialConfigController(parent=self)
        dialog.exec()