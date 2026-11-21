import logging
from PySide6.QtCore import QThread, Signal
from models.repository import TelemetryRepository


class DatabaseQueryWorker(QThread):
    """
    Thread de segundo plano para consultas no SQLite.
    Garante que a interface gráfica permaneça 100% responsiva (sem congelar)
    mesmo durante consultas volumosas de histórico de leituras.
    """

    consulta_concluida = Signal(list)
    erro_ocorrido = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tipo_consulta = "ultimos"
        self._limite = 50
        self._data_inicio = ""
        self._data_fim = ""

    def configurar_ultimos(self, limite: int):
        """Define o filtro por últimas N leituras."""
        self._tipo_consulta = "ultimos"
        self._limite = max(1, int(limite))

    def configurar_intervalo(self, data_inicio: str, data_fim: str):
        """Define o filtro por intervalo de data/hora (formato 'YYYY-MM-DD HH:MM:SS')."""
        self._tipo_consulta = "intervalo"
        self._data_inicio = data_inicio
        self._data_fim = data_fim

    def run(self):
        """Executa a consulta parametrizada no banco em segundo plano."""
        try:
            if self._tipo_consulta == "ultimos":
                dados = TelemetryRepository.consultar_ultimos(self._limite)
            elif self._tipo_consulta == "intervalo":
                dados = TelemetryRepository.consultar_por_intervalo(
                    self._data_inicio, self._data_fim
                )
            else:
                dados = []

            self.consulta_concluida.emit(dados)
        except Exception as exc:
            logging.exception("Falha ao executar consulta ao SQLite em segundo plano: %s", exc)
            self.erro_ocorrido.emit(str(exc))
