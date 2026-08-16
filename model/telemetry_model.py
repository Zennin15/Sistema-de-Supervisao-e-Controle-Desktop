import random
import time
from collections import deque


class TelemetryModel:
    """
    Model responsável pelos dados de telemetria (Tensão, Corrente e Potência).

    - Manter o buffer/histórico das amostras (timestamp, V, I, P) para o gráfico de
      tendência temporal.
    - Calcular a Potência Ativa a partir de P = V x I.
    - Fornecer os dados já tratados para o Controller (a View nunca acessa este
      objeto diretamente, seguindo o padrão MVC).

    """

    TENSAO_NOMINAL = 220.0      # V - tensão de referência da rede simulada
    CORRENTE_NOMINAL = 5.0      # A - corrente de referência simulada
    TAMANHO_HISTORICO = 60      # quantidade de amostras mantidas no buffer (ex.: 60s)

    def __init__(self, tamanho_historico: int = TAMANHO_HISTORICO):
        self.tamanho_historico = tamanho_historico

        # Buffers circulares com o histórico de amostras (usados pelo gráfico)
        self.historico_tempo = deque(maxlen=tamanho_historico)
        self.historico_tensao = deque(maxlen=tamanho_historico)
        self.historico_corrente = deque(maxlen=tamanho_historico)
        self.historico_potencia = deque(maxlen=tamanho_historico)

        self.tensao_atual = 0.0
        self.corrente_atual = 0.0
        self.potencia_atual = 0.0

        self._contador_amostras = 0

        # Requisito: o gráfico deve abrir com histórico pré-carregado
        self._pre_carregar_historico()

    # ------------------------------------------------------------------
    # Cálculo / registro de amostras
    # ------------------------------------------------------------------
    def calcular_potencia(self, tensao: float, corrente: float) -> float:
        """Calcula a Potência Ativa aproximada: P = V x I (Watts)."""
        return tensao * corrente

    def registrar_amostra(self, tensao: float, corrente: float) -> dict:
        """
        Calcula a potência e atualiza o histórico.

        Retorna um dicionário com a amostra tratada, pronto para a View exibir.
        """
        potencia = self.calcular_potencia(tensao, corrente)

        self.tensao_atual = tensao
        self.corrente_atual = corrente
        self.potencia_atual = potencia

        self._contador_amostras += 1
        self.historico_tempo.append(self._contador_amostras)
        self.historico_tensao.append(tensao)
        self.historico_corrente.append(corrente)
        self.historico_potencia.append(potencia)

        return {
            "tempo": self._contador_amostras,
            "tensao": tensao,
            "corrente": corrente,
            "potencia": potencia,
        }

    def gerar_amostra_simulada(self) -> dict:
       
        tensao = round(random.uniform(
            self.TENSAO_NOMINAL - 8, self.TENSAO_NOMINAL + 8), 2)
        corrente = round(random.uniform(
            max(0.0, self.CORRENTE_NOMINAL - 1.5), self.CORRENTE_NOMINAL + 1.5), 2)

        return self.registrar_amostra(tensao, corrente)

    # ------------------------------------------------------------------
    # Histórico / consultas para a View
    # ------------------------------------------------------------------
    def _pre_carregar_historico(self) -> None:
        """Preenche o buffer com um histórico inicial simulado, para que o
        gráfico não abra vazio (requisito de histórico pré-carregado)."""
        for _ in range(self.tamanho_historico):
            self.gerar_amostra_simulada()

    def get_historico(self) -> dict:
        """Retorna o histórico completo (listas) usado para plotar o gráfico."""
        return {
            "tempo": list(self.historico_tempo),
            "tensao": list(self.historico_tensao),
            "corrente": list(self.historico_corrente),
            "potencia": list(self.historico_potencia),
        }

    def get_valores_atuais(self) -> dict:
        """Retorna os últimos valores instantâneos (para os indicadores/LCDs)."""
        return {
            "tensao": self.tensao_atual,
            "corrente": self.corrente_atual,
            "potencia": self.potencia_atual,
        }
