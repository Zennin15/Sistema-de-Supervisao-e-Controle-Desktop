from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ui.dashboard_window import Ui_DashboardWindow
from model.telemetry_model import TelemetryModel


class DashboardWindowController(QDialog):
    """
    Controller da tela de Dashboard (padrão MVC).

    - View  -> ui/dashboard_window.py (Ui_DashboardWindow), gerado a partir do
               dashboard_window.ui montado no Qt Designer.
    - Model -> model/telemetry_model.py (TelemetryModel): cálculo de potência,
               histórico/curva de demanda, estado do disjuntor e limite de alerta.
    - Controller (esta classe) -> liga o Model à View: alimenta os QLCDNumber,
               o LED do disjuntor, o gráfico Matplotlib, e trata os comandos
               (corte emergencial e ajuste do limite de alerta). A atualização
               periódica é simulada via QTimer nesta entrega; futuramente será
               disparada pela chegada de dados na porta serial.
    """

    INTERVALO_ATUALIZACAO_MS = 1000  # 1 amostra por segundo

    COR_LED_FECHADO = "#00E676"
    COR_LED_ABERTO = "#D32F2F"

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- View ---
        self.ui = Ui_DashboardWindow()
        self.ui.setupUi(self)

        # --- Model ---
        self.model = TelemetryModel()

        # --- Gráfico Matplotlib embutido no placeholder criado no Designer ---
        self._configurar_grafico()

        # Carrega o histórico/estado inicial do Model assim que a tela abre
        self._carregar_estado_inicial()

        # --- Conexões ---
        self.ui.botaoVoltar.clicked.connect(self.close)
        self.ui.botaoCorteEmergencial.clicked.connect(self.acionar_corte_emergencial)
        self.ui.sliderLimiteAlerta.valueChanged.connect(self.ajustar_limite_alerta)

        # --- Timer de atualização (fonte simulada de telemetria) ---
        self.timer_telemetria = QTimer(self)
        self.timer_telemetria.setInterval(self.INTERVALO_ATUALIZACAO_MS)
        self.timer_telemetria.timeout.connect(self.atualizar_telemetria)
        self.timer_telemetria.start()

    # ------------------------------------------------------------------
    # Configuração do gráfico
    # ------------------------------------------------------------------
    def _configurar_grafico(self):
        """Cria a Figure/Canvas do Matplotlib e o insere dentro do QWidget
        'widgetGrafico' definido no arquivo .ui (montado no Designer)."""
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.eixo = self.figure.add_subplot(111)

        self.eixo.set_title("Curva de Demanda - Consumo de Potência (W)")
        self.eixo.set_xlabel("Amostra (histórico 24h + tempo real)")
        self.eixo.set_ylabel("Potência (W)")
        self.eixo.grid(True, linestyle="--", alpha=0.4)

        (self.linha_potencia,) = self.eixo.plot([], [], color="#00A86B", linewidth=1.8)

        # Linha de referência do limite de alerta, atualizada quando o slider muda
        self.linha_limite = self.eixo.axhline(
            self.model.limite_alerta_watts, color="#D32F2F",
            linestyle="--", linewidth=1.2, label="Limite de alerta")
        self.eixo.legend(loc="upper right", fontsize=8)

        # O placeholder já possui um layout vazio definido no .ui;
        # basta adicionar o canvas nele.
        self.ui.widgetGrafico.layout().addWidget(self.canvas)

    def _carregar_estado_inicial(self):
        """Requisito: o gráfico deve abrir com histórico pré-carregado (curva
        de demanda de 24h) e os demais indicadores já refletindo o Model."""
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(valores["tensao"], valores["corrente"], valores["potencia"])
        self._atualizar_estado_disjuntor()

        self.ui.labelStatus.setText("Status: histórico de 24h carregado — simulação ativa")

    # ------------------------------------------------------------------
    # Atualização periódica (chamada pelo QTimer / futuramente pela serial)
    # ------------------------------------------------------------------
    def atualizar_telemetria(self):
        """Obtém uma nova amostra do Model (simulada) e atualiza a View."""
        amostra = self.model.gerar_amostra_simulada()

        self._atualizar_indicadores(amostra["tensao"], amostra["corrente"], amostra["potencia"])

        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        status = f"Status: última amostra #{amostra['tempo']}"
        if not self.model.disjuntor_fechado:
            status = "Status: disjuntor ABERTO — carga cortada"
        self.ui.labelStatus.setText(status)

    def receber_amostra_real(self, tensao: float, corrente: float):
        """
        Ponto de integração futuro: quando a leitura via serial estiver
        disponível, basta chamar este método com os valores reais de
        VRMS/IRMS lidos do microcontrolador, no lugar da amostra simulada.
        """
        amostra = self.model.registrar_amostra(tensao, corrente)

        self._atualizar_indicadores(amostra["tensao"], amostra["corrente"], amostra["potencia"])

        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

    # ------------------------------------------------------------------
    # Comandos de acionamento
    # ------------------------------------------------------------------
    def acionar_corte_emergencial(self):
        """Botão 'Corte Emergencial de Carga': alterna o disjuntor/relé.
        Fechado -> abre a chave e zera V/I/P. Aberto -> rearma a chave."""
        self.model.alternar_disjuntor()
        self._atualizar_estado_disjuntor()

        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(valores["tensao"], valores["corrente"], valores["potencia"])

        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

    def ajustar_limite_alerta(self, valor: int):
        """Slider de ajuste visual do limite de alerta de consumo (Watts)."""
        self.model.set_limite_alerta(valor)
        self.ui.labelLimiteAlerta.setText(f"Limite de Alerta de Consumo: {valor} W")

        # Atualiza a linha de referência no gráfico
        self.linha_limite.set_ydata([valor, valor])
        self.canvas.draw_idle()

        self._atualizar_alerta_visual()

    # ------------------------------------------------------------------
    # Atualização dos widgets da View
    # ------------------------------------------------------------------
    def _atualizar_indicadores(self, tensao: float, corrente: float, potencia: float):
        self.ui.lcdTensao.display(tensao)
        self.ui.lcdCorrente.display(corrente)
        self.ui.lcdPotencia.display(potencia)
        self._atualizar_alerta_visual()

    def _atualizar_estado_disjuntor(self):
        """Atualiza o LED virtual e o texto do estado do disjuntor (Aberto/Fechado)."""
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
        """Mostra/esconde o aviso de consumo acima do limite e destaca o LCD
        de potência quando o alerta está ativo."""
        acima_do_limite = self.model.consumo_acima_do_limite()
        self.ui.labelAlerta.setVisible(acima_do_limite)

        cor = "#D32F2F" if acima_do_limite else "#00E676"
        self.ui.lcdPotencia.setStyleSheet(
            f"QLCDNumber {{ background-color: #101820; color: {cor}; "
            f"border: 2px solid {cor}; border-radius: 6px; }}"
        )

    def _redesenhar_grafico(self, eixo_x, eixo_y):
        self.linha_potencia.set_data(eixo_x, eixo_y)

        self.eixo.relim()
        self.eixo.autoscale_view()

        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Garante que o timer pare quando a janela for fechada."""
        self.timer_telemetria.stop()
        super().closeEvent(event)
