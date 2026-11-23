from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QSpinBox, QDateTimeEdit, QPushButton, QLabel
)
from PySide6.QtCore import Signal, QDateTime

class PainelGraficoView(QWidget):
    modo_alterado = Signal(str)
    consulta_solicitada = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo_atual = "tempo_real"
        self._buffer_tempo_real = []
        self._montar_ui()

    def _montar_ui(self):
        layout = QVBoxLayout(self)
        barra = QHBoxLayout()

        self.combo_modo = QComboBox()
        self.combo_modo.addItem("Monitoramento em Tempo Real", "tempo_real")
        self.combo_modo.addItem("Consulta de Historico", "historico")
        self.combo_modo.currentIndexChanged.connect(self._ao_trocar_modo)

        self.combo_tipo_filtro = QComboBox()
        self.combo_tipo_filtro.addItem("Ultimas N leituras", "ultimas_n")
        self.combo_tipo_filtro.addItem("Intervalo de Data/Hora", "intervalo")
        self.combo_tipo_filtro.currentIndexChanged.connect(self._atualizar_visibilidade_filtros)

        self.spin_n = QSpinBox()
        self.spin_n.setRange(10, 10000)
        self.spin_n.setValue(100)
        self.spin_n.setPrefix("N = ")

        self.dt_inicio = QDateTimeEdit(QDateTime.currentDateTime().addSecs(-3600))
        self.dt_inicio.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_inicio.setCalendarPopup(True)

        self.dt_fim = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_fim.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_fim.setCalendarPopup(True)

        self.btn_buscar = QPushButton("Carregar Historico")
        self.btn_buscar.clicked.connect(self._emitir_busca)

        barra.addWidget(QLabel("Modo do Grafico:"))
        barra.addWidget(self.combo_modo)
        barra.addWidget(self.combo_tipo_filtro)
        barra.addWidget(self.spin_n)
        barra.addWidget(self.dt_inicio)
        barra.addWidget(self.dt_fim)
        barra.addWidget(self.btn_buscar)
        barra.addStretch()

        layout.addLayout(barra)
        self._atualizar_visibilidade_filtros()

    def _ao_trocar_modo(self):
        self._modo_atual = self.combo_modo.currentData()
        self._atualizar_visibilidade_filtros()
        self.modo_alterado.emit(self._modo_atual)
        if self._modo_atual == "tempo_real":
            self.plotar_serie(self._buffer_tempo_real)

    def _atualizar_visibilidade_filtros(self):
        eh_historico = self._modo_atual == "historico"
        tipo = self.combo_tipo_filtro.currentData()
        self.combo_tipo_filtro.setVisible(eh_historico)
        self.spin_n.setVisible(eh_historico and tipo == "ultimas_n")
        self.dt_inicio.setVisible(eh_historico and tipo == "intervalo")
        self.dt_fim.setVisible(eh_historico and tipo == "intervalo")
        self.btn_buscar.setVisible(eh_historico)

    def _emitir_busca(self):
        self.consulta_solicitada.emit({
            "tipo_filtro": self.combo_tipo_filtro.currentData(),
            "limite_n": self.spin_n.value(),
            "data_inicio": self.dt_inicio.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "data_fim": self.dt_fim.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
        })

    def adicionar_ponto_tempo_real(self, leitura: dict):
        self._buffer_tempo_real.append(leitura)
        if len(self._buffer_tempo_real) > 60:
            self._buffer_tempo_real.pop(0)
        if self._modo_atual == "tempo_real":
            self.plotar_serie(self._buffer_tempo_real)

    def plotar_serie(self, registros: list[dict]):
        self._ultimos_dados_plotados = registros
