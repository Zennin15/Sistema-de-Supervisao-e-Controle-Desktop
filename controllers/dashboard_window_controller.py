import logging
import os
import sqlite3

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QDialog, QMessageBox

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

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
    """Controller do dashboard, incluindo a persistência dos comandos e alarmes."""

    INTERVALO_ATUALIZACAO_MS = 1000
    COR_LED_FECHADO = "#00E676"
    COR_LED_ABERTO = "#D32F2F"

    # A tela principal escuta esse sinal para recarregar a tabela apos o commit.
    historico_atualizado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_DashboardWindow()
        self.ui.setupUi(self)
        self.model = TelemetryModel()
        self._alerta_ativo = False
        self._carregar_estado_persistido()

        self._configurar_grafico()
        self._carregar_estado_inicial()

        self.ui.botaoVoltar.clicked.connect(self.close)
        self.ui.botaoCorteEmergencial.clicked.connect(self.acionar_corte_emergencial)
        self.ui.sliderLimiteAlerta.valueChanged.connect(self.ajustar_limite_alerta)

        self.timer_telemetria = QTimer(self)
        self.timer_telemetria.setInterval(self.INTERVALO_ATUALIZACAO_MS)
        self.timer_telemetria.timeout.connect(self.atualizar_telemetria)
        self.timer_telemetria.start()

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
    # Gráfico e estado inicial
    # ------------------------------------------------------------------
    def _configurar_grafico(self):
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.eixo = self.figure.add_subplot(111)
        self.eixo.set_title("Curva de Demanda - Consumo de Potência (W)")
        self.eixo.set_xlabel("Amostra (histórico 24h + tempo real)")
        self.eixo.set_ylabel("Potência (W)")
        self.eixo.grid(True, linestyle="--", alpha=0.4)
        (self.linha_potencia,) = self.eixo.plot([], [], color="#00A86B", linewidth=1.8)
        self.linha_limite = self.eixo.axhline(
            self.model.limite_alerta_watts,
            color="#D32F2F",
            linestyle="--",
            linewidth=1.2,
            label="Limite de alerta",
        )
        self.eixo.legend(loc="upper right", fontsize=8)
        self.ui.widgetGrafico.layout().addWidget(self.canvas)

    def _carregar_estado_inicial(self):
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )
        self._atualizar_estado_disjuntor()
        self.ui.labelStatus.setText("Status: histórico de 24h carregado - simulação ativa")

    # ------------------------------------------------------------------
    # Telemetria
    # ------------------------------------------------------------------
    def atualizar_telemetria(self):
        amostra = self.model.gerar_amostra_simulada()
        self._atualizar_indicadores(
            amostra["tensao"], amostra["corrente"], amostra["potencia"]
        )
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        status = f"Status: última amostra #{amostra['tempo']}"
        if not self.model.disjuntor_fechado:
            status = "Status: disjuntor ABERTO - carga cortada"
        self.ui.labelStatus.setText(status)

    def receber_amostra_real(self, tensao: float, corrente: float):
        """Ponto futuro de integração com dados lidos pela porta serial."""
        amostra = self.model.registrar_amostra(tensao, corrente)
        self._atualizar_indicadores(
            amostra["tensao"], amostra["corrente"], amostra["potencia"]
        )
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

    # ------------------------------------------------------------------
    # Comandos persistidos
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

                # Gancho de teste para demonstrar ROLLBACK na apresentação.
                # Defina SMARTGRID_SIMULAR_FALHA_CORTE=1 antes de iniciar o app.
                if os.environ.get("SMARTGRID_SIMULAR_FALHA_CORTE", "").strip() == "1":
                    raise RuntimeError(
                        "Falha de teste simulada antes do registro de histórico."
                    )

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

        # Só altera o Model depois de confirmar que o banco fez o commit.
        if novo_status == "ABERTO":
            self.model.abrir_disjuntor()
        else:
            self.model.fechar_disjuntor()

        self._atualizar_estado_disjuntor()
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )
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
    # Widgets, alertas e registro no banco
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
        """Exibe o alarme e persiste apenas a transição para estado de alerta."""
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
        self.timer_telemetria.stop()
        super().closeEvent(event)
