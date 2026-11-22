import logging
import sqlite3
from datetime import datetime

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
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
from logs.logger import registrar_erro_emergencia
from models.repository import (
    ActuatorRepository,
    LimitRepository,
    Repository,
    TAG_DISJUNTOR_PRINCIPAL,
)
from ui.main_window import Ui_MainWindow


class _DbTaskSignals(QObject):
    """Sinais para entregar resultados de threads do banco para a Main Thread."""

    historico_carregado = Signal(list)
    limites_carregados = Signal(list)
    evento_registrado = Signal(bool, str, object)
    limites_salvos = Signal(bool, list, str)
    erro_db = Signal(str, str)


class _DbTask(QRunnable):
    """Executa operações do banco fora da GUI thread."""

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)


class MainWindowController(QMainWindow):
    """
    Main Thread (GUI): gerencia janelas, cliques, navegação e renderização da UI.
    Operações de banco são passadas para o QThreadPool para não bloquear a interface.
    """

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._thread_pool = QThreadPool.globalInstance()
        self._db_signals = _DbTaskSignals()
        self._db_signals.historico_carregado.connect(self._renderizar_historico)
        self._db_signals.limites_carregados.connect(self._on_limites_carregados)
        self._db_signals.evento_registrado.connect(self._on_evento_registrado)
        self._db_signals.limites_salvos.connect(self._on_limites_salvos)
        self._db_signals.erro_db.connect(self._on_erro_db)

        self.limites_registrados = []
        self._consultar_limites_async()

        # Botão de fechar histórico posicionado acima da tabela.
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

        # Conexões dos botões da janela principal.
        if hasattr(self.ui, "pushButton_4"):
            self.ui.pushButton_4.clicked.connect(self.abrir_janela)
        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.clicked.connect(self.exibir_historico)
        if hasattr(self.ui, "pushButton_3"):
            self.ui.pushButton_3.clicked.connect(self.abrir_dashboard)
        if hasattr(self.ui, "pushButton_2"):
            self.ui.pushButton_2.clicked.connect(self.abrir_configuracao_serial)

    def showEvent(self, event):
        """Solicita atualização assíncrona da tabela quando a janela é exibida."""
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

    def _consultar_limites_async(self):
        def tarefa():
            try:
                limites = LimitRepository.listar_todos()
                self._db_signals.limites_carregados.emit(limites)
            except sqlite3.Error as exc:
                logging.exception("Falha ao carregar os limites persistidos.")
                self._db_signals.erro_db.emit(
                    "Erro ao carregar limites",
                    f"Não foi possível consultar os limites no SQLite.\n{exc}",
                )

        self._thread_pool.start(_DbTask(tarefa))

    def _on_limites_carregados(self, limites: list):
        self.limites_registrados = limites

    def carregar_historico(self):
        """Dispara a consulta do histórico em worker thread sem bloquear a GUI."""
        if not hasattr(self.ui, "tableEventos"):
            return

        def tarefa():
            try:
                eventos = Repository.listar_todos()
                self._db_signals.historico_carregado.emit(eventos)
            except sqlite3.Error:
                logging.exception("Falha ao consultar o histórico de eventos no SQLite.")

        self._thread_pool.start(_DbTask(tarefa))

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
                    tabela.setItem(row, coluna, QTableWidgetItem(str(conteudo)))
        finally:
            tabela.setUpdatesEnabled(True)

    def registrar_evento(self, tipo: str, descricao: str, valor_medido=None):
        """Persiste um evento em background e atualiza a tabela ao concluir."""

        def tarefa():
            try:
                atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
                Repository.registrar_evento(
                    tipo_evento=tipo,
                    descricao=descricao,
                    valor_medido=valor_medido,
                    atuador_id=atuador_id,
                )
                eventos = Repository.listar_todos()
                self._db_signals.evento_registrado.emit(True, tipo, descricao)
                self._db_signals.historico_carregado.emit(eventos)
            except (sqlite3.Error, ValueError) as exc:
                logging.exception("Falha ao registrar evento no SQLite.")
                if "emerg" in tipo.lower() or "corte" in tipo.lower():
                    registrar_erro_emergencia(str(exc))
                self._db_signals.erro_db.emit(
                    "Erro de persistência",
                    f"Não foi possível registrar o evento no histórico.\n{exc}",
                )

        self._thread_pool.start(_DbTask(tarefa))

    def _on_evento_registrado(self, sucesso: bool, tipo: str, descricao: str):
        if sucesso:
            logging.info("Evento registrado: %s - %s", tipo, descricao)

    def _on_erro_db(self, titulo: str, mensagem: str):
        QMessageBox.critical(self, titulo, mensagem)

    def exibir_historico(self):
        """Atualiza e exibe a tabela e o botão de fechar."""
        self.carregar_historico()
        if hasattr(self.ui, "tableEventos"):
            self.ui.tableEventos.setVisible(True)
            if hasattr(self, "btn_fechar_historico"):
                self.btn_fechar_historico.setVisible(True)

    def fechar_historico(self):
        """Oculta a tabela e o botão de fechar."""
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

        def tarefa():
            try:
                LimitRepository.substituir_todos(novos_limites)
                for idx, limite in enumerate(novos_limites, start=1):
                    tensao = limite.get("Tensao", "-")
                    corrente = limite.get("Corrente", "-")
                    atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
                    Repository.registrar_evento(
                        tipo_evento="Configuração",
                        descricao=(
                            f"Regra #{idx}: Tensão máxima={tensao} V, "
                            f"corrente máxima={corrente} A"
                        ),
                        valor_medido=None,
                        atuador_id=atuador_id,
                    )
                eventos = Repository.listar_todos()
                self._db_signals.limites_salvos.emit(True, novos_limites, "")
                self._db_signals.historico_carregado.emit(eventos)
            except (sqlite3.Error, ValueError, KeyError) as exc:
                logging.exception("Falha ao persistir os limites de segurança.")
                self._db_signals.limites_salvos.emit(
                    False,
                    novos_limites,
                    f"Não foi possível salvar os limites.\n{exc}",
                )

        self._thread_pool.start(_DbTask(tarefa))

    def _on_limites_salvos(self, sucesso: bool, novos_limites: list, erro_msg: str):
        if sucesso:
            self.limites_registrados = novos_limites
            QMessageBox.information(
                self, "Sucesso", "Limites salvos no SQLite e registrados no histórico!"
            )
        else:
            QMessageBox.critical(self, "Erro ao salvar limites", erro_msg)

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