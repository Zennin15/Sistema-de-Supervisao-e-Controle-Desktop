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
from controllers.database_worker import DatabaseWorker
from controllers.limits_configuration_window_controller import LimitsConfigurationWindowController
from controllers.serial_controller import SerialConfigController
from controllers.serial_worker import SerialWorker
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

        # Referência persistente à SerialWorker ativa (sobrevive ao fechamento
        # do diálogo de configuração), usada para refletir o estado real da
        # conexão ao reabrir a tela e para alimentar o dashboard com dados reais.
        self.serial_worker_ativo: SerialWorker | None = None

        # Thread dedicada de persistência: grava continuamente as leituras de
        # telemetria recebidas da SerialWorker, sem bloquear a GUI.
        self.database_worker = DatabaseWorker(self)
        self.database_worker.erro_persistencia.connect(self._on_erro_persistencia)
        self.database_worker.start()

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

    def closeEvent(self, event):
        """Encerra as threads em segundo plano com segurança ao fechar o app."""
        if self.serial_worker_ativo is not None and self.serial_worker_ativo.isRunning():
            self.serial_worker_ativo.parar()
        self.database_worker.parar()
        super().closeEvent(event)

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
        dashboard = DashboardWindowController(parent=self, worker_ativo=self.serial_worker_ativo)
        dashboard.historico_atualizado.connect(self.carregar_historico)
        dashboard.exec()
        self.carregar_historico()

    def abrir_configuracao_serial(self):
        dialog = SerialConfigController(parent=self, worker_ativo=self.serial_worker_ativo)
        if hasattr(dialog, "status_alterado"):
            dialog.status_alterado.connect(self._registrar_status_serial)
        dialog.worker_iniciado.connect(self._on_worker_serial_iniciado)
        dialog.exec()

    def _on_worker_serial_iniciado(self, worker: SerialWorker):
        """Passa a escutar a worker diretamente, independente do diálogo estar aberto."""
        self.serial_worker_ativo = worker
        worker.conexao_alterada.connect(self._on_conexao_serial_alterada)
        worker.erro_serial.connect(self._on_erro_serial_worker)
        # Cada leitura válida decodificada passa a ser gravada continuamente
        # no SQLite pela DatabaseWorker, em segundo plano (sem travar a GUI).
        worker.leitura_para_gravar.connect(self.database_worker.gravar_leitura_telemetria)
        # Confirmação visível (no histórico) de que um comando de corte/rearme
        # foi de fato escrito na porta serial - ajuda a diagnosticar se a
        # placa não reagiu por falta de envio ou por outro motivo.
        worker.comando_enviado.connect(self._on_comando_serial_enviado)

    def _on_comando_serial_enviado(self, comando: str):
        self.registrar_evento("Comando serial enviado", f"Comando enviado à placa: {comando}")

    def _on_erro_persistencia(self, titulo: str, mensagem: str):
        QMessageBox.warning(self, titulo, mensagem)

    def _on_conexao_serial_alterada(self, conectado: bool, mensagem: str):
        if not conectado and self.sender() is self.serial_worker_ativo:
            self.serial_worker_ativo = None

    def _on_erro_serial_worker(self, mensagem: str):
        """Exibe apenas um aviso na tela; nunca deixa a exceção se propagar
        (ex.: cabo USB removido fisicamente durante a comunicação)."""
        QMessageBox.warning(self, "Aviso de Comunicação Serial", mensagem)

    def _registrar_status_serial(self, conectado: bool, dados: dict):
        status = "Conexão serial estabelecida" if conectado else "Conexão serial encerrada"
        porta = dados.get("porta", "desconhecida")
        baud_rate = dados.get("baud_rate", "desconhecido")
        self.registrar_evento(status, f"Porta {porta}, baud rate {baud_rate} bps")
