import logging
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
)

from controllers.dashboard_window_controller import DashboardWindowController
from controllers.database_worker import DatabaseWorker
from controllers.limits_configuration_window_controller import LimitsConfigurationWindowController
from controllers.serial_controller import SerialConfigController
from controllers.serial_worker import SerialWorker
from logs.logger import registrar_alerta_corrente
from models.repository import TAG_DISJUNTOR_PRINCIPAL
from ui.main_window import Ui_MainWindow


class MainWindowController(QMainWindow):
    """
    Main Thread (GUI): gerencia janelas, cliques, navegação e renderização da UI.
    - SerialWorker (QThread): leitura contínua da porta serial e decodificação de pacotes.
    - DatabaseWorker (QThread): persistência e consultas SQLite isoladas em segundo plano.
    """

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.limites_registrados = []
        self.serial_worker: SerialWorker | None = None

        # 1. Database Worker Thread dedicada
        self.db_worker = DatabaseWorker(parent=self)
        self.db_worker.historico_carregado.connect(self._renderizar_historico)
        self.db_worker.limites_carregados.connect(self._on_limites_carregados)
        self.db_worker.limites_gravados.connect(self._on_limites_gravados)
        self.db_worker.evento_gravado.connect(self._on_evento_gravado)
        self.db_worker.erro_persistencia.connect(self._on_erro_db)
        self.db_worker.start()

        # Botão de fechar histórico posicionado acima da tabela
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

        # Conexões dos botões da janela principal
        if hasattr(self.ui, "pushButton_4"):
            self.ui.pushButton_4.clicked.connect(self.abrir_janela)
        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.clicked.connect(self.exibir_historico)
        if hasattr(self.ui, "pushButton_3"):
            self.ui.pushButton_3.clicked.connect(self.abrir_dashboard)
        if hasattr(self.ui, "pushButton_2"):
            self.ui.pushButton_2.clicked.connect(self.abrir_configuracao_serial)

        # Carga inicial em segundo plano
        self.db_worker.solicitar_limites()
        self.db_worker.solicitar_historico()

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_historico()

    def closeEvent(self, event):
        """Encerra SerialWorker e DatabaseWorker de forma ordenada."""
        if self.serial_worker is not None and self.serial_worker.isRunning():
            self.serial_worker.parar()
            self.serial_worker = None

        if hasattr(self, "db_worker") and self.db_worker.isRunning():
            self.db_worker.parar()

        super().closeEvent(event)

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
        if not hasattr(self.ui, "tableEventos"):
            return
        self.db_worker.solicitar_historico()

    def _renderizar_historico(self, eventos: list):
        """Atualiza a QTableWidget exclusivamente na Main Thread."""
        if not hasattr(self.ui, "tableEventos"):
            return

        tabela = self.ui.tableEventos
        tabela.setUpdatesEnabled(False)
        try:
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
                    item = QTableWidgetItem(str(conteudo))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    tabela.setItem(row, coluna, item)
        finally:
            tabela.setUpdatesEnabled(True)

    def registrar_evento(self, tipo: str, descricao: str, valor_medido=None):
        self.db_worker.gravar_evento(
            tipo_evento=tipo,
            descricao=descricao,
            valor_medido=valor_medido,
            tag_atuador=TAG_DISJUNTOR_PRINCIPAL,
        )

    def _on_evento_gravado(self, tipo: str, descricao: str, valor_medido):
        logging.info("Evento registrado: %s - %s", tipo, descricao)

    def _on_limites_carregados(self, limites: list):
        self.limites_registrados = limites

    def _on_limites_gravados(self, novos_limites: list):
        self.limites_registrados = novos_limites
        for idx, limite in enumerate(novos_limites, start=1):
            tensao = limite.get("Tensao", "-")
            corrente = limite.get("Corrente", "-")
            self.registrar_evento(
                "Configuração",
                f"Regra #{idx}: Tensão máxima={tensao} V, corrente máxima={corrente} A",
            )
        QMessageBox.information(
            self, "Sucesso", "Limites salvos no SQLite e registrados no histórico!"
        )

    def _on_erro_db(self, titulo: str, mensagem: str):
        QMessageBox.critical(self, titulo, mensagem)

    def exibir_historico(self):
        self.carregar_historico()
        if hasattr(self.ui, "tableEventos"):
            self.ui.tableEventos.setVisible(True)
            if hasattr(self, "btn_fechar_historico"):
                self.btn_fechar_historico.setVisible(True)

    def fechar_historico(self):
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
        self.db_worker.substituir_limites(novos_limites)

    def abrir_dashboard(self):
        dashboard = DashboardWindowController(parent=self)
        if hasattr(dashboard, "historico_atualizado"):
            dashboard.historico_atualizado.connect(self.carregar_historico)

        # Se o worker serial estiver ativo, repassa leituras decodificadas para o dashboard
        if self.serial_worker is not None and hasattr(dashboard, "atualizar_leitura"):
            self.serial_worker.dados_recebidos.connect(dashboard.atualizar_leitura)

        dashboard.exec()

        if self.serial_worker is not None and hasattr(dashboard, "atualizar_leitura"):
            try:
                self.serial_worker.dados_recebidos.disconnect(dashboard.atualizar_leitura)
            except (RuntimeError, TypeError):
                pass

        self.carregar_historico()

    def abrir_configuracao_serial(self):
        dialog = SerialConfigController(
            parent=self,
            worker_ativo=self.serial_worker,
        )
        dialog.worker_iniciado.connect(self._vincular_worker_serial)
        dialog.worker_encerrado.connect(self._desvincular_worker_serial)
        dialog.status_alterado.connect(self._registrar_status_serial)
        dialog.exec()

    def _vincular_worker_serial(self, worker: SerialWorker):
        """Mantém o worker ativo no controller principal e liga aos subsistemas."""
        if self.serial_worker is not None and self.serial_worker is not worker:
            self.serial_worker.parar()

        self.serial_worker = worker
        self.serial_worker.leitura_para_gravar.connect(self.db_worker.gravar_leitura_telemetria)
        self.serial_worker.dados_recebidos.connect(self._verificar_limites_leitura)
        self.serial_worker.erro_serial.connect(self._on_erro_serial)
        self.serial_worker.finished.connect(self._on_worker_serial_finalizado)

    def _desvincular_worker_serial(self):
        self.serial_worker = None

    def _on_worker_serial_finalizado(self):
        self.serial_worker = None

    def _verificar_limites_leitura(self, pacote: dict):
        """Avalia corrente recebida contra os limites configurados e registra alerta se exceder."""
        corrente = pacote.get("corrente")
        if corrente is None or not self.limites_registrados:
            return

        for regra in self.limites_registrados:
            try:
                limite_corrente = float(regra.get("Corrente", 0))
            except (TypeError, ValueError):
                continue

            if limite_corrente > 0 and float(corrente) > limite_corrente:
                registrar_alerta_corrente(float(corrente), limite_corrente)
                break

    def _on_erro_serial(self, mensagem: str):
        QMessageBox.warning(self, "Erro de Comunicação Serial", mensagem)

    def _registrar_status_serial(self, conectado: bool, dados: dict):
        status = "Conexão serial estabelecida" if conectado else "Conexão serial encerrada"
        porta = dados.get("porta", "desconhecida")
        baud_rate = dados.get("baud_rate", "desconhecido")
        self.registrar_evento(status, f"Porta {porta}, baud rate {baud_rate} bps")