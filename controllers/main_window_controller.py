import logging
import sqlite3
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
)

from controllers.dashboard_window_controller import DashboardWindowController
from controllers.limits_configuration_window_controller import LimitsConfigurationWindowController
from controllers.serial_controller import SerialConfigController
from models.repository import (
    ActuatorRepository,
    LimitRepository,
    Repository,
    TAG_DISJUNTOR_PRINCIPAL,
)
from ui.main_window import Ui_MainWindow


class MainWindowController(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        try:
            self.limites_registrados = LimitRepository.listar_todos()
        except sqlite3.Error:
            logging.exception("Falha ao carregar os limites persistidos.")
            self.limites_registrados = []

        # Criar botao de fechar histórico dinamicamente acima da tabela.
        if hasattr(self.ui, "tableEventos"):
            self.btn_fechar_historico = QPushButton("Fechar Histórico", self.ui.centralwidget)
            self.btn_fechar_historico.setGeometry(
                self.ui.tableEventos.x() + self.ui.tableEventos.width() - 130,
                self.ui.tableEventos.y() - 25,
                130,
                23,
            )
            self.btn_fechar_historico.clicked.connect(self.fechar_historico)
            self.btn_fechar_historico.setVisible(False)
            self.ui.tableEventos.setVisible(False)

        self.configurar_tabela_eventos()

        # Conexoes dos botoes da janela principal.
        if hasattr(self.ui, "pushButton_4"):
            self.ui.pushButton_4.clicked.connect(self.abrir_janela)
        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.clicked.connect(self.exibir_historico)
        if hasattr(self.ui, "pushButton_3"):
            self.ui.pushButton_3.clicked.connect(self.abrir_dashboard)
        if hasattr(self.ui, "pushButton_2"):
            self.ui.pushButton_2.clicked.connect(self.abrir_configuracao_serial)

    def showEvent(self, event):
        """Atualiza a tabela diretamente do repositório sempre que a janela abre."""
        super().showEvent(event)
        self.carregar_historico()

    def configurar_tabela_eventos(self):
        if not hasattr(self.ui, "tableEventos"):
            return

        self.ui.tableEventos.setColumnCount(4)
        self.ui.tableEventos.setHorizontalHeaderLabels(
            ["Data/Hora", "Tipo de Evento", "Valor Medido", "Descrição"]
        )
        header = self.ui.tableEventos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

    @staticmethod
    def _formatar_data_hora(valor):
        if not valor:
            return ""
        try:
            data_hora = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
            return data_hora.strftime("%d/%m/%Y %H:%M:%S")
        except (TypeError, ValueError):
            return str(valor)

    def carregar_historico(self):
        """Carrega os registros persistidos; nao utiliza eventos estaticos em memoria."""
        if not hasattr(self.ui, "tableEventos"):
            return
        try:
            eventos = Repository.listar_todos()
        except sqlite3.Error:
            logging.exception("Falha ao consultar o histórico de eventos no SQLite.")
            return

        tabela = self.ui.tableEventos
        tabela.setRowCount(0)
        for evento in eventos:
            row = tabela.rowCount()
            tabela.insertRow(row)
            valor = evento["valor_medido"]
            valor_formatado = "-" if valor is None else f"{valor:g}"
            itens = (
                self._formatar_data_hora(evento["data_hora"]),
                evento["tipo_evento"],
                valor_formatado,
                evento["descricao"],
            )
            for coluna, conteudo in enumerate(itens):
                tabela.setItem(row, coluna, QTableWidgetItem(str(conteudo)))

    def registrar_evento(self, tipo: str, descricao: str, valor_medido=None):
        """Persiste um evento e atualiza a tabela a partir do SQLite."""
        try:
            atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            Repository.registrar_evento(
                tipo_evento=tipo,
                descricao=descricao,
                valor_medido=valor_medido,
                atuador_id=atuador_id,
            )
            self.carregar_historico()
            logging.info("Evento registrado: %s - %s", tipo, descricao)
            return True
        except (sqlite3.Error, ValueError) as exc:
            logging.exception("Falha ao registrar evento no SQLite.")
            QMessageBox.critical(
                self,
                "Erro de persistência",
                f"Não foi possível registrar o evento no histórico.\n{exc}",
            )
            return False

    def exibir_historico(self):
        """Atualiza e exibe a tabela e o botao de fechar."""
        self.carregar_historico()
        if hasattr(self.ui, "tableEventos"):
            self.ui.tableEventos.setVisible(True)
            if hasattr(self, "btn_fechar_historico"):
                self.btn_fechar_historico.setVisible(True)

    def fechar_historico(self):
        """Oculta a tabela e o botao de fechar."""
        if hasattr(self.ui, "tableEventos"):
            self.ui.tableEventos.setVisible(False)
            if hasattr(self, "btn_fechar_historico"):
                self.btn_fechar_historico.setVisible(False)

    def abrir_janela(self):
        popup = LimitsConfigurationWindowController(parent=self)
        popup.carregar_dados(self.limites_registrados)

        if popup.exec() != QDialog.Accepted:
            return

        novos_limites = popup.get_dados()
        try:
            LimitRepository.substituir_todos(novos_limites)
            self.limites_registrados = novos_limites
            for idx, limite in enumerate(self.limites_registrados, start=1):
                tensao = limite.get("Tensao", "-")
                corrente = limite.get("Corrente", "-")
                if not self.registrar_evento(
                    "Configuração",
                    f"Regra #{idx}: Tensão máxima={tensao} V, corrente máxima={corrente} A",
                ):
                    return
            QMessageBox.information(
                self, "Sucesso", "Limites salvos no SQLite e registrados no histórico!"
            )
        except (sqlite3.Error, ValueError, KeyError) as exc:
            logging.exception("Falha ao persistir os limites de segurança.")
            QMessageBox.critical(
                self,
                "Erro ao salvar limites",
                f"Não foi possível salvar os limites.\n{exc}",
            )

    def abrir_dashboard(self):
        dashboard = DashboardWindowController(parent=self)
        dashboard.historico_atualizado.connect(self.carregar_historico)
        dashboard.exec()
        self.carregar_historico()

    def abrir_configuracao_serial(self):
        dialog = SerialConfigController(parent=self)
        if hasattr(dialog, "status_alterado"):
            dialog.status_alterado.connect(self._registrar_status_serial)
        dialog.exec()

    def _registrar_status_serial(self, conectado: bool, dados: dict):
        status = "Conexão serial estabelecida" if conectado else "Conexão serial encerrada"
        porta = dados.get("porta", "desconhecida")
        baud_rate = dados.get("baud_rate", "desconhecido")
        self.registrar_evento(status, f"Porta {porta}, baud rate {baud_rate} bps")
