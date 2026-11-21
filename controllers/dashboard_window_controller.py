import logging
import os
import sqlite3
from datetime import datetime

from PySide6.QtCore import QDateTime, Signal
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from controllers.db_worker import DatabaseQueryWorker
from controllers.serial_worker import SerialReaderThread
from database.connection import Database
from logger import registrar_erro_emergencia
from models.repository import (
    ActuatorRepository,
    Repository,
    TAG_DISJUNTOR_PRINCIPAL,
    TAG_RELE_EMERGENCIA,
)
from models.telemetry_model import TelemetryModel
from ui.dashboard_window import Ui_DashboardWindow


class DashboardWindowController(QDialog):
    """
    Controller do dashboard de telemetria.
    
    Implementa o Requisito 5:
    - Modo Monitoramento em Tempo Real: Atualizado continuamente via thread serial (SerialReaderThread).
    - Modo Consulta de Histórico: Busca assíncrona no SQLite via thread de segundo plano (DatabaseQueryWorker),
      permitindo analisar oscilações passadas sem travar a interface gráfica.
    """

    COR_LED_FECHADO = "#00E676"
    COR_LED_ABERTO = "#D32F2F"

    # A tela principal escuta esse sinal para recarregar a tabela após alterações de atuadores
    historico_atualizado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_DashboardWindow()
        self.ui.setupUi(self)
        self.model = TelemetryModel()
        self._alerta_ativo = False
        self._modo_tempo_real = True

        self._carregar_estado_persistido()
        self._configurar_grafico()
        self._configurar_painel_modos_e_filtros()
        self._carregar_estado_inicial()

        # Conexões dos botões existentes
        self.ui.botaoVoltar.clicked.connect(self.close)
        self.ui.botaoCorteEmergencial.clicked.connect(self.acionar_corte_emergencial)
        self.ui.sliderLimiteAlerta.valueChanged.connect(self.ajustar_limite_alerta)

        # --------------------------------------------------------------
        # Threads em Segundo Plano
        # --------------------------------------------------------------
        # 1. Thread de Banco de Dados (consultas pesadas assíncronas)
        self.db_worker = DatabaseQueryWorker(self)
        self.db_worker.consulta_concluida.connect(self._ao_concluir_consulta_historico)
        self.db_worker.erro_ocorrido.connect(self._ao_falhar_consulta_historico)

        # 2. Thread Serial (leitura e telemetria contínua)
        self.serial_thread = SerialReaderThread(parent=self)
        self.serial_thread.definir_corte_carga(not self.model.disjuntor_fechado)
        self.serial_thread.amostra_recebida.connect(self.receber_amostra_serial)
        self.serial_thread.status_conexao.connect(self._ao_atualizar_status_serial)
        self.serial_thread.start()

    def _carregar_estado_persistido(self):
        """Sincroniza o estado inicial do disjuntor com o banco."""
        try:
            atuador = ActuatorRepository.obter_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            if atuador:
                self.model.disjuntor_fechado = atuador["status"] == "FECHADO"
                if not self.model.disjuntor_fechado:
                    self.model.registrar_amostra(0.0, 0.0)
        except sqlite3.Error:
            logging.exception("Não foi possível carregar o estado persistido do disjuntor.")

    # ------------------------------------------------------------------
    # Configuração da Interface Gráfica e Modos
    # ------------------------------------------------------------------
    def _configurar_grafico(self):
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.eixo = self.figure.add_subplot(111)
        self.eixo.set_title("Curva de Demanda - Consumo em Tempo Real (W)")
        self.eixo.set_xlabel("Amostras Recentes")
        self.eixo.set_ylabel("Potência (W)")
        self.eixo.grid(True, linestyle="--", alpha=0.4)
        (self.linha_potencia,) = self.eixo.plot([], [], color="#00A86B", linewidth=1.8, label="Potência Ativa")
        self.linha_limite = self.eixo.axhline(
            self.model.limite_alerta_watts,
            color="#D32F2F",
            linestyle="--",
            linewidth=1.2,
            label="Limite de alerta",
        )
        self.eixo.legend(loc="upper right", fontsize=8)
        self.ui.widgetGrafico.layout().addWidget(self.canvas)

    def _configurar_painel_modos_e_filtros(self):
        """
        Adiciona os controles de alternância entre Modo Tempo Real e Consulta de Histórico,
        além dos filtros de busca por N leituras ou intervalo de datas.
        """
        self.groupBoxModos = QGroupBox("Modo de Operação do Gráfico Principal", self)
        layout_modos = QVBoxLayout(self.groupBoxModos)

        # Seleção de Modo (RadioButtons)
        linha_selecao_modo = QHBoxLayout()
        self.radioTempoReal = QRadioButton("🟢 Modo Monitoramento em Tempo Real (Thread Serial)")
        self.radioHistorico = QRadioButton("📜 Modo Consulta de Histórico (Thread SQLite)")
        self.radioTempoReal.setChecked(True)
        self.radioTempoReal.toggled.connect(self._alternar_modo_operacao)

        linha_selecao_modo.addWidget(self.radioTempoReal)
        linha_selecao_modo.addWidget(self.radioHistorico)
        linha_selecao_modo.addStretch()
        layout_modos.addLayout(linha_selecao_modo)

        # Painel de Filtros de Histórico (visível apenas no modo histórico)
        self.frameFiltroHistorico = QFrame(self.groupBoxModos)
        layout_filtro = QHBoxLayout(self.frameFiltroHistorico)
        layout_filtro.setContentsMargins(0, 4, 0, 0)

        # Opção 1: Últimas N leituras
        self.radioFiltroUltimos = QRadioButton("Últimas:")
        self.radioFiltroUltimos.setChecked(True)
        self.spinUltimosN = QSpinBox()
        self.spinUltimosN.setRange(5, 5000)
        self.spinUltimosN.setValue(50)
        self.spinUltimosN.setSingleStep(10)
        self.spinUltimosN.setSuffix(" leituras")

        # Opção 2: Intervalo de Data/Hora
        self.radioFiltroIntervalo = QRadioButton("Período:")
        self.dtInicio = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.dtInicio.setCalendarPopup(True)
        self.dtInicio.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.lblAte = QLabel("até")
        self.dtFim = QDateTimeEdit(QDateTime.currentDateTime())
        self.dtFim.setCalendarPopup(True)
        self.dtFim.setDisplayFormat("dd/MM/yyyy HH:mm:ss")

        # Botão de Busca
        self.btnConsultarHistorico = QPushButton("🔍 Consultar SQLite")
        self.btnConsultarHistorico.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #1976D2; color: white; "
            "padding: 5px 12px; border-radius: 4px; } QPushButton:hover { background-color: #1565C0; }"
        )
        self.btnConsultarHistorico.clicked.connect(self._solicitar_consulta_historico)

        # Botão Retornar ao Tempo Real
        self.btnRetornarTempoReal = QPushButton("▶ Retornar ao Tempo Real")
        self.btnRetornarTempoReal.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #00A86B; color: white; "
            "padding: 5px 12px; border-radius: 4px; } QPushButton:hover { background-color: #008f5a; }"
        )
        self.btnRetornarTempoReal.clicked.connect(lambda: self.radioTempoReal.setChecked(True))

        layout_filtro.addWidget(self.radioFiltroUltimos)
        layout_filtro.addWidget(self.spinUltimosN)
        layout_filtro.addSpacing(12)
        layout_filtro.addWidget(self.radioFiltroIntervalo)
        layout_filtro.addWidget(self.dtInicio)
        layout_filtro.addWidget(self.lblAte)
        layout_filtro.addWidget(self.dtFim)
        layout_filtro.addSpacing(12)
        layout_filtro.addWidget(self.btnConsultarHistorico)
        layout_filtro.addWidget(self.btnRetornarTempoReal)
        layout_filtro.addStretch()

        layout_modos.addWidget(self.frameFiltroHistorico)
        self.frameFiltroHistorico.setVisible(False)

        # Insere o painel na interface principal logo acima do gráfico
        self.ui.verticalLayoutPrincipal.insertWidget(4, self.groupBoxModos)

    def _carregar_estado_inicial(self):
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )
        self._atualizar_estado_disjuntor()

    # ------------------------------------------------------------------
    # Alternância de Modos e Consulta Histórica
    # ------------------------------------------------------------------
    def _alternar_modo_operacao(self, tempo_real_ativo: bool):
        """Alterna a interface entre Monitoramento em Tempo Real e Consulta de Histórico."""
        self._modo_tempo_real = tempo_real_ativo
        self.frameFiltroHistorico.setVisible(not tempo_real_ativo)

        if tempo_real_ativo:
            self.eixo.set_title("Curva de Demanda - Consumo em Tempo Real (W)")
            self.eixo.set_xlabel("Amostras Recentes")
            historico = self.model.get_historico()
            self._redesenhar_grafico(historico["tempo"], historico["potencia"])
            self.ui.labelStatus.setText("Status: Modo Tempo Real ativo (Thread serial atualizando gráfico)")
        else:
            self.eixo.set_title("Curva de Demanda - Consulta de Histórico (SQLite)")
            self.eixo.set_xlabel("Amostras Históricas")
            self.ui.labelStatus.setText("Status: Modo Histórico ativo. Defina o filtro e clique em 'Consultar SQLite'.")

    def _solicitar_consulta_historico(self):
        """
        Inicia a busca no banco de dados SQLite através da thread de segundo plano (DatabaseQueryWorker).
        Não bloqueia a usabilidade da aplicação.
        """
        if self.db_worker.isRunning():
            return

        self.btnConsultarHistorico.setEnabled(False)
        self.ui.labelStatus.setText("Status: Consultando histórico no SQLite em segundo plano...")

        if self.radioFiltroUltimos.isChecked():
            n = self.spinUltimosN.value()
            self.db_worker.configurar_ultimos(n)
        else:
            data_ini = self.dtInicio.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            data_fim = self.dtFim.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            if self.dtInicio.dateTime() > self.dtFim.dateTime():
                QMessageBox.warning(self, "Filtro Inválido", "A data inicial deve ser anterior à data final.")
                self.btnConsultarHistorico.setEnabled(True)
                return
            self.db_worker.configurar_intervalo(data_ini, data_fim)

        self.db_worker.start()

    def _ao_concluir_consulta_historico(self, dados: list):
        """
        Slot executado na thread da GUI quando o DatabaseQueryWorker conclui a busca.
        Replota imediatamente a curva no gráfico principal com os registros retornados.
        """
        self.btnConsultarHistorico.setEnabled(True)

        if not dados:
            QMessageBox.information(self, "Consulta Vazia", "Nenhuma leitura encontrada para o filtro selecionado.")
            self.ui.labelStatus.setText("Status: Consulta concluída — 0 registros encontrados.")
            return

        # Extrai potências e gera índices das amostras
        potencias = [d["potencia"] for d in dados]
        eixo_x = list(range(1, len(potencias) + 1))

        self.eixo.set_title(f"Consulta de Histórico SQLite ({len(dados)} leituras carregadas)")
        self.eixo.set_xlabel(f"Amostras Históricas ({dados[0]['data_hora']} até {dados[-1]['data_hora']})")
        self._redesenhar_grafico(eixo_x, potencias)

        self.ui.labelStatus.setText(
            f"Status: {len(dados)} leituras carregadas do SQLite via thread de segundo plano."
        )

    def _ao_falhar_consulta_historico(self, mensagem_erro: str):
        """Trata falha na consulta assíncrona."""
        self.btnConsultarHistorico.setEnabled(True)
        QMessageBox.critical(self, "Erro no Banco", f"Falha na consulta ao histórico:\n{mensagem_erro}")
        self.ui.labelStatus.setText("Status: Falha ao consultar histórico no banco de dados.")

    # ------------------------------------------------------------------
    # Telemetria em Tempo Real (Thread Serial)
    # ------------------------------------------------------------------
    def receber_amostra_serial(self, amostra: dict):
        """
        Recebe cada nova amostra gerada pela Thread Serial em tempo real.
        Se o modo for Tempo Real, atualiza imediatamente os displays e a curva do gráfico.
        """
        tensao = amostra["tensao"]
        corrente = amostra["corrente"]
        potencia = amostra["potencia"]

        # Registra a amostra no modelo em memória
        self.model.registrar_amostra(tensao, corrente)

        # Sempre atualiza os LCDs de status atual
        self._atualizar_indicadores(tensao, corrente, potencia)

        # Atualiza a curva gráfica somente se estiver no Modo Tempo Real
        # (evita sobrescrever a visualização enquanto o operador analisa dados históricos passados)
        if self._modo_tempo_real:
            historico = self.model.get_historico()
            self._redesenhar_grafico(historico["tempo"], historico["potencia"])

            status = f"Status: Tempo Real - Amostra #{amostra.get('data_hora', '')} | Potência: {potencia:.1f} W"
            if not self.model.disjuntor_fechado:
                status = "Status: disjuntor ABERTO - carga cortada"
            self.ui.labelStatus.setText(status)

    def _ao_atualizar_status_serial(self, conectado: bool, mensagem: str):
        """Atualiza informações da porta serial no status bar."""
        if self._modo_tempo_real:
            self.ui.labelStatus.setText(f"Status Serial: {mensagem}")

    # ------------------------------------------------------------------
    # Comandos persistidos e Corte Emergencial
    # ------------------------------------------------------------------
    def acionar_corte_emergencial(self):
        """Atualiza disjuntor, relé e histórico em uma única transação ACID."""
        novo_status = "ABERTO" if self.model.disjuntor_fechado else "FECHADO"
        if novo_status == "ABERTO":
            tipo_evento = "Corte emergencial"
            descricao = "Disjuntor principal e relé de emergência abertos; carga cortada."
        else:
            tipo_evento = "Rearme do disjuntor"
            descricao = "Disjuntor principal e relé de emergência fechados; carga restabelecida."

        conn = Database.get_connection()
        try:
            with conn:
                atuador = ActuatorRepository.obter_por_tag(
                    TAG_DISJUNTOR_PRINCIPAL, conn
                )
                if atuador is None:
                    raise ValueError("Disjuntor principal não cadastrado no banco.")

                ActuatorRepository.atualizar_status_por_tag(
                    conn, TAG_DISJUNTOR_PRINCIPAL, novo_status
                )
                ActuatorRepository.atualizar_status_por_tag(
                    conn, TAG_RELE_EMERGENCIA, novo_status
                )

                if os.environ.get("SMARTGRID_SIMULAR_FALHA_CORTE", "").strip() == "1":
                    raise RuntimeError("Falha de teste simulada antes do registro de histórico.")

                Repository.inserir_em_conexao(
                    conn,
                    tipo_evento,
                    descricao,
                    self.model.potencia_atual,
                    atuador["id"],
                )
        except Exception as exc:
            registrar_erro_emergencia(str(exc))
            QMessageBox.critical(
                self,
                "Falha no corte emergencial",
                "A operação não foi concluída. O banco foi revertido (ROLLBACK).\n"
                f"Motivo: {exc}",
            )
            return
        finally:
            conn.close()

        # Atualiza modelo e comunica corte de carga à thread serial
        if novo_status == "ABERTO":
            self.model.abrir_disjuntor()
            self.serial_thread.definir_corte_carga(True)
        else:
            self.model.fechar_disjuntor()
            self.serial_thread.definir_corte_carga(False)

        self._atualizar_estado_disjuntor()
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )

        if self._modo_tempo_real:
            historico = self.model.get_historico()
            self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        self.ui.labelStatus.setText(
            "Status: disjuntor ABERTO - carga cortada"
            if novo_status == "ABERTO"
            else "Status: disjuntor FECHADO - carga restabelecida"
        )
        logging.info("%s concluído com sucesso.", tipo_evento)
        self.historico_atualizado.emit()

    def ajustar_limite_alerta(self, valor: int):
        self.model.set_limite_alerta(valor)
        self.ui.labelLimiteAlerta.setText(f"Limite de Alerta de Consumo: {valor} W")
        self.linha_limite.set_ydata([valor, valor])
        self.canvas.draw_idle()
        self._atualizar_alerta_visual()

    # ------------------------------------------------------------------
    # Widgets e Alertas
    # ------------------------------------------------------------------
    def _atualizar_indicadores(self, tensao: float, corrente: float, potencia: float):
        self.ui.lcdTensao.display(tensao)
        self.ui.lcdCorrente.display(corrente)
        self.ui.lcdPotencia.display(potencia)
        self._atualizar_alerta_visual()

    def _atualizar_estado_disjuntor(self):
        if self.model.disjuntor_fechado:
            cor = self.COR_LED_FECHADO
            self.ui.labelTextoDisjuntor.setText("FECHADO")
            self.ui.botaoCorteEmergencial.setText("CORTE EMERGENCIAL DE CARGA")
        else:
            cor = self.COR_LED_ABERTO
            self.ui.labelTextoDisjuntor.setText("ABERTO")
            self.ui.botaoCorteEmergencial.setText("REARMAR DISJUNTOR")

        self.ui.labelLedDisjuntor.setStyleSheet(
            f"QLabel {{ background-color: {cor}; border: 2px solid #0a3d1f; border-radius: 21px; }}"
        )

    def _atualizar_alerta_visual(self):
        acima_do_limite = self.model.consumo_acima_do_limite()
        self.ui.labelAlerta.setVisible(acima_do_limite)

        cor = "#D32F2F" if acima_do_limite else "#00E676"
        self.ui.lcdPotencia.setStyleSheet(
            f"QLCDNumber {{ background-color: #101820; color: {cor}; "
            f"border: 2px solid {cor}; border-radius: 6px; }}"
        )

        if acima_do_limite and not self._alerta_ativo:
            self._registrar_evento_alarme()
        self._alerta_ativo = acima_do_limite

    def _registrar_evento_alarme(self):
        potencia = self.model.potencia_atual
        limite = self.model.limite_alerta_watts
        descricao = (
            f"Potência acima do limite: {potencia:.2f} W "
            f"(limite configurado: {limite:.2f} W)."
        )
        try:
            atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            Repository.registrar_evento(
                "Alarme de consumo", descricao, potencia, atuador_id
            )
            logging.warning(descricao)
            self.historico_atualizado.emit()
        except (sqlite3.Error, ValueError) as exc:
            logging.exception("Falha ao persistir o evento de alarme: %s", exc)

    def _redesenhar_grafico(self, eixo_x, eixo_y):
        self.linha_potencia.set_data(eixo_x, eixo_y)
        self.eixo.relim()
        self.eixo.autoscale_view()
        self.canvas.draw_idle()

    def closeEvent(self, event):
        """Encerra com segurança as threads em execução ao fechar a janela."""
        if hasattr(self, "serial_thread") and self.serial_thread.isRunning():
            self.serial_thread.parar()
        if hasattr(self, "db_worker") and self.db_worker.isRunning():
            self.db_worker.wait(1000)
        super().closeEvent(event)
