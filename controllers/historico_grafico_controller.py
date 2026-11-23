from controllers.consulta_historico_worker import ConsultaHistoricoWorker

class HistoricoGraficoControllerMixin:
    def configurar_grafico_e_historico(self, painel_grafico, db_path: str = "smartgrid.db"):
        self.painel_grafico = painel_grafico
        self.db_path = db_path
        self._worker_historico = None
        self.painel_grafico.consulta_solicitada.connect(self.executar_consulta_historica)

    def executar_consulta_historica(self, filtros: dict):
        if self._worker_historico is not None and self._worker_historico.isRunning():
            self._worker_historico.wait(500)

        self._worker_historico = ConsultaHistoricoWorker(
            db_path=self.db_path,
            tipo_filtro=filtros["tipo_filtro"],
            limite_n=filtros["limite_n"],
            data_inicio=filtros["data_inicio"],
            data_fim=filtros["data_fim"],
        )
        self._worker_historico.historico_carregado.connect(self.painel_grafico.plotar_serie)
        self._worker_historico.start()
