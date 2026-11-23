from PySide6.QtCore import QThread, Signal
from models.historico_repository import HistoricoRepository

class ConsultaHistoricoWorker(QThread):
    historico_carregado = Signal(list)
    erro_consulta = Signal(str)

    def __init__(
        self,
        db_path: str = "smartgrid.db",
        tipo_filtro: str = "ultimas_n",
        limite_n: int = 100,
        data_inicio: str = "",
        data_fim: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.repo = HistoricoRepository(db_path)
        self.tipo_filtro = tipo_filtro
        self.limite_n = limite_n
        self.data_inicio = data_inicio
        self.data_fim = data_fim

    def run(self):
        try:
            if self.tipo_filtro == "ultimas_n":
                dados = self.repo.buscar_ultimas_leituras(self.limite_n)
            else:
                dados = self.repo.buscar_por_intervalo(self.data_inicio, self.data_fim)
            self.historico_carregado.emit(dados)
        except Exception as exc:
            self.erro_consulta.emit(f"Falha ao consultar historico: {exc}")
