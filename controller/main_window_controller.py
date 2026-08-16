from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem, QMessageBox, QHeaderView
from PySide6.QtCore import QDateTime
from ui.main_window import Ui_MainWindow

# Importa o controlador da janela modal que você criou
from controller.config_controller import ConfigDialogController

class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Configura a tabela de histórico de eventos
        self.configurar_tabela_eventos()

        # Conecta o botão de abrir configurações
        if hasattr(self.ui, 'btnAbrirConfig'):
            self.ui.btnAbrirConfig.clicked.connect(self.abrir_dialogo_config)

    def configurar_tabela_eventos(self):
        """Define os cabeçalhos e ajusta a largura das colunas da QTableWidget."""
        if hasattr(self.ui, 'tableEventos'):
            self.ui.tableEventos.setColumnCount(3)
            self.ui.tableEventos.setHorizontalHeaderLabels(["Data/Hora", "Tipo de Evento", "Descrição"])
            
            # Ajusta o tamanho das colunas para preencher a tabela sem cortar texto
            header = self.ui.tableEventos.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.Stretch)

    def registrar_evento(self, tipo: str, descricao: str):
        """Insere uma nova linha na QTableWidget."""
        if hasattr(self.ui, 'tableEventos'):
            row_position = self.ui.tableEventos.rowCount()
            self.ui.tableEventos.insertRow(row_position)

            data_hora = QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm:ss")

            self.ui.tableEventos.setItem(row_position, 0, QTableWidgetItem(data_hora))
            self.ui.tableEventos.setItem(row_position, 1, QTableWidgetItem(tipo))
            self.ui.tableEventos.setItem(row_position, 2, QTableWidgetItem(descricao))

    def abrir_dialogo_config(self):
        """Abre o modal QDialog de configurações."""
        dialog = ConfigDialogController(self)
        dialog.regras_salvas.connect(self.atualizar_parametros_alerta)
        dialog.exec()

    def atualizar_parametros_alerta(self, dados_regras: dict):
        """Recebe as regras salvas do modal e registra no histórico de eventos."""
        limite_c = dados_regras["corrente_max"]
        limite_t = dados_regras["tensao_max"]

        self.registrar_evento("Configuração", f"Limites atualizados: Corrente Max={limite_c}A, Tensão Max={limite_t}V")
        QMessageBox.information(self, "Sucesso", "Regras de alerta salvas e aplicadas com sucesso!")