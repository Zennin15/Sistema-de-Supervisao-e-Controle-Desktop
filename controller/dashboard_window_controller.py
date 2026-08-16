from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ui.dashboard_window import Ui_DashboardWindow
from model.telemetry_model import TelemetryModel


class DashboardWindowController(QDialog):

    INTERVALO_ATUALIZACAO_MS = 1000  # 1 amostra por segundo

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- View ---
        self.ui = Ui_DashboardWindow()
        self.ui.setupUi(self)

        # --- Model ---
        self.model = TelemetryModel()

        # --- Gráfico Matplotlib embutido no placeholder criado no Designer ---
        self._configurar_grafico()

        # Carrega o histórico pré-existente do Model assim que a tela abre
        self._carregar_historico_inicial()

        # --- Conexões ---
        self.ui.botaoVoltar.clicked.connect(self.close)

        # --- Timer de atualização (fonte simulada) ---
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

        self.eixo.set_title("Consumo de Potência (W)")
        self.eixo.set_xlabel("Amostra")
        self.eixo.set_ylabel("Potência (W)")
        self.eixo.grid(True, linestyle="--", alpha=0.4)

        (self.linha_potencia,) = self.eixo.plot([], [], color="#00A86B", linewidth=1.8)

        # O placeholder já possui um layout vazio definido no .ui;
        # basta adicionar o canvas nele.
        self.ui.widgetGrafico.layout().addWidget(self.canvas)

    def _carregar_historico_inicial(self):
        """Requisito: o gráfico deve abrir com histórico pré-carregado."""
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(valores["tensao"], valores["corrente"], valores["potencia"])

        self.ui.labelStatus.setText("Status: histórico carregado — simulação ativa")

    # ------------------------------------------------------------------
    # Atualização periódica (chamada pelo QTimer / futuramente pela serial)
    # ------------------------------------------------------------------
    def atualizar_telemetria(self):
        """Obtém uma nova amostra do Model (simulada) e atualiza a View."""
        amostra = self.model.gerar_amostra_simulada()

        self._atualizar_indicadores(amostra["tensao"], amostra["corrente"], amostra["potencia"])

        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

        self.ui.labelStatus.setText(f"Status: última amostra #{amostra['tempo']}")

    def receber_amostra_real(self, tensao: float, corrente: float):
        amostra = self.model.registrar_amostra(tensao, corrente)

        self._atualizar_indicadores(amostra["tensao"], amostra["corrente"], amostra["potencia"])

        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])

    # ------------------------------------------------------------------
    # Atualização dos widgets da View
    # ------------------------------------------------------------------
    def _atualizar_indicadores(self, tensao: float, corrente: float, potencia: float):
        self.ui.lcdTensao.display(tensao)
        self.ui.lcdCorrente.display(corrente)
        self.ui.lcdPotencia.display(potencia)

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
