import random
from collections import deque


class TelemetryModel:
    """
    Model responsável pelos dados de telemetria (Tensão, Corrente e Potência),
    pelo estado do disjuntor/chave de proteção e pelo limite de alerta de consumo.

    - Mantém o buffer/histórico das amostras (V, I, P) usado no gráfico de
      tendência, pré-carregado com uma curva de demanda simulada de 24 horas.
    - Calcula a Potência Ativa a partir de P = V x I.
    - Controla o estado binário do disjuntor (Fechado/Aberto) e o corte
      emergencial de carga.
    - Guarda o limite de alerta de consumo (ajustável pela View) e informa se
      a potência atual o ultrapassou.

    A View nunca acessa este objeto diretamente sem passar pelo Controller,
    seguindo o padrão MVC.
    """

    TENSAO_NOMINAL = 220.0        # V - tensão de referência da rede simulada
    CORRENTE_NOMINAL = 5.0        # A - corrente de referência simulada
    TAMANHO_HISTORICO = 24        # 24 pontos = curva de demanda das últimas 24h

    # Padrão relativo de consumo ao longo de 24 horas (0h à 23h), usado apenas
    # para gerar a carga inicial do gráfico com uma "cara" de curva de demanda
    # real (baixo consumo de madrugada, picos de manhã/noite).
    PADRAO_DEMANDA_24H = [
        0.30, 0.25, 0.22, 0.20, 0.22, 0.30, 0.45, 0.65,
        0.75, 0.70, 0.68, 0.72, 0.78, 0.75, 0.70, 0.68,
        0.72, 0.85, 0.95, 0.90, 0.75, 0.60, 0.45, 0.35,
    ]

    LIMITE_ALERTA_PADRAO_W = 1500.0

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

        # --- Disjuntor / Chave de proteção ---
        self.disjuntor_fechado = True  # True = Fechado (energizado) / False = Aberto

        # --- Limite de alerta de consumo (ajustável pela View) ---
        self.limite_alerta_watts = self.LIMITE_ALERTA_PADRAO_W

        # Requisito: o gráfico deve abrir com histórico pré-carregado
        # (curva de demanda simulada das últimas 24 horas)
        self._pre_carregar_curva_24h()

    # ------------------------------------------------------------------
    # Cálculo / registro de amostras
    # ------------------------------------------------------------------
    def calcular_potencia(self, tensao: float, corrente: float) -> float:
        """Calcula a Potência Ativa aproximada: P = V x I (Watts)."""
        return tensao * corrente

    def registrar_amostra(self, tensao: float, corrente: float) -> dict:
        """
        Calcula a potência e atualiza o histórico.
        Se o disjuntor estiver aberto, a carga foi cortada: V/I/P são zerados,
        independentemente do valor lido/simulado.
        """
        if not self.disjuntor_fechado:
            tensao, corrente = 0.0, 0.0

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
        """Gera uma amostra simulada de V e I com ruído, imitando um sensor
        real (ACS712 / ZMPT101B), e registra essa amostra."""
        tensao = round(random.uniform(
            self.TENSAO_NOMINAL - 8, self.TENSAO_NOMINAL + 8), 2)
        corrente = round(random.uniform(
            max(0.0, self.CORRENTE_NOMINAL - 1.5), self.CORRENTE_NOMINAL + 1.5), 2)

        return self.registrar_amostra(tensao, corrente)

    # ------------------------------------------------------------------
    # Disjuntor / Chave de proteção
    # ------------------------------------------------------------------
    def abrir_disjuntor(self) -> None:
        """Executa o corte emergencial de carga (relé): abre o disjuntor,
        cortando a energia — V, I e P passam a ser 0."""
        self.disjuntor_fechado = False
        self.registrar_amostra(0.0, 0.0)

    def fechar_disjuntor(self) -> None:
        """Rearma/fecha o disjuntor, restabelecendo a energia."""
        self.disjuntor_fechado = True

    def alternar_disjuntor(self) -> bool:
        """Alterna o estado do disjuntor. Retorna o novo estado (True=Fechado)."""
        if self.disjuntor_fechado:
            self.abrir_disjuntor()
        else:
            self.fechar_disjuntor()
        return self.disjuntor_fechado

    # ------------------------------------------------------------------
    # Limite de alerta de consumo
    # ------------------------------------------------------------------
    def set_limite_alerta(self, valor_watts: float) -> None:
        """Atualiza o limite de alerta de consumo (ajustado pela View)."""
        self.limite_alerta_watts = float(valor_watts)

    def consumo_acima_do_limite(self) -> bool:
        """Indica se a potência atual ultrapassou o limite de alerta."""
        return self.potencia_atual > self.limite_alerta_watts

    # ------------------------------------------------------------------
    # Histórico / consultas para a View
    # ------------------------------------------------------------------
    def _pre_carregar_curva_24h(self) -> None:
        """Preenche o buffer com uma curva de demanda simulada das últimas 24
        horas, para que o gráfico já abra com dados renderizados (requisito
        de carga inicial), em vez de abrir vazio."""
        for fator in self.PADRAO_DEMANDA_24H:
            corrente = round(
                self.CORRENTE_NOMINAL * fator + random.uniform(-0.1, 0.1), 2)
            tensao = round(random.uniform(
                self.TENSAO_NOMINAL - 5, self.TENSAO_NOMINAL + 5), 2)
            self.registrar_amostra(tensao, max(0.0, corrente))

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
