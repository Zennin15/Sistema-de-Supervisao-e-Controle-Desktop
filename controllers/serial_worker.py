import logging
import random
import time
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from models.repository import TelemetryRepository


class SerialReaderThread(QThread):
    """
    Thread de segundo plano para aquisição de telemetria da rede elétrica.
    Opera continuamente sem travar a interface gráfica (GUI).
    
    Cada nova amostra lida (ou gerada por simulação realista quando a porta física
    não estiver presente) é persistida no banco SQLite e emitida imediatamente via sinal
    para atualizar a curva gráfica e os displays em tempo real.
    """

    amostra_recebida = Signal(dict)
    status_conexao = Signal(bool, str)

    TENSAO_NOMINAL = 220.0
    CORRENTE_NOMINAL = 5.0

    def __init__(self, porta: str = "COM3", baud_rate: int = 9600, parent=None):
        super().__init__(parent)
        self.porta = porta
        self.baud_rate = baud_rate
        self._executando = False
        self._carga_cortada = False

    def definir_corte_carga(self, cortada: bool):
        """Ajusta se o disjuntor cortou a carga (tensão e corrente passam a 0)."""
        self._carga_cortada = cortada

    def parar(self):
        """Encerra a execução da thread com segurança."""
        self._executando = False
        self.quit()
        self.wait(2000)

    def run(self):
        self._executando = True
        conexao_serial = None
        porta_aberta = False

        # Tenta conexão física caso pyserial esteja instalado e a porta disponível
        try:
            import serial
            conexao_serial = serial.Serial(self.porta, self.baud_rate, timeout=1.0)
            porta_aberta = conexao_serial.is_open
            self.status_conexao.emit(True, f"Conectado à {self.porta} ({self.baud_rate} bps)")
            logging.info("Thread serial conectada à %s com %d bps", self.porta, self.baud_rate)
        except Exception:
            self.status_conexao.emit(False, f"Modo Simulado ativo ({self.porta} indisponível)")
            logging.info("Porta %s não disponível. Operando no modo telemetria simulada contínua.", self.porta)

        while self._executando:
            try:
                if porta_aberta and conexao_serial and conexao_serial.is_open:
                    linha = conexao_serial.readline().decode("utf-8", errors="ignore").strip()
                    if linha:
                        tensao, corrente = self._extrair_valores_linha(linha)
                    else:
                        time.sleep(0.1)
                        continue
                else:
                    # Simulação realista com ruído e variação contínua da rede elétrica
                    time.sleep(1.0)
                    if self._carga_cortada:
                        tensao = 0.0
                        corrente = 0.0
                    else:
                        tensao = round(random.uniform(self.TENSAO_NOMINAL - 6.0, self.TENSAO_NOMINAL + 6.0), 2)
                        corrente = round(random.uniform(max(0.0, self.CORRENTE_NOMINAL - 1.2), self.CORRENTE_NOMINAL + 1.2), 2)

                potencia = round(tensao * corrente, 2)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Gravação contínua no banco de dados SQLite para consulta histórica
                try:
                    TelemetryRepository.salvar_leitura(tensao, corrente, potencia, timestamp)
                except Exception as db_err:
                    logging.error("Falha ao salvar amostra serial no SQLite: %s", db_err)

                dados_amostra = {
                    "data_hora": timestamp,
                    "tensao": tensao,
                    "corrente": corrente,
                    "potencia": potencia,
                }

                # Notifica a interface gráfica imediatamente via sinal Qt
                self.amostra_recebida.emit(dados_amostra)

            except Exception as exc:
                logging.error("Erro no ciclo de leitura serial: %s", exc)
                time.sleep(1.0)

        if conexao_serial and conexao_serial.is_open:
            try:
                conexao_serial.close()
            except Exception:
                pass
        logging.info("Thread serial encerrada com sucesso.")

    def _extrair_valores_linha(self, linha: str):
        """Converte dados recebidos da serial (suporta formatos como 'V:220.0,I:4.5' ou '220.0,4.5' ou '220.0;4.5')."""
        linha_limpa = linha.replace("V:", "").replace("I:", "").replace(";", ",")
        partes = linha_limpa.split(",")
        tensao = float(partes[0].strip())
        corrente = float(partes[1].strip()) if len(partes) > 1 else 0.0
        return tensao, corrente
