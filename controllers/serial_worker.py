import json
import logging
import time
from PySide6.QtCore import QThread, Signal

try:
    import serial  # pyserial
except ImportError:
    serial = None


class SerialWorker(QThread):
    """
    QThread dedicada à comunicação serial:
    - Abre a porta e executa o handshake inicial
    - Lê pacotes continuamente sem bloquear a GUI
    - Emite sinais com dados decodificados para displays e persistência
    """

    # Sinais para a camada de UI / Controller / Persistência
    conexao_alterada = Signal(bool, str)       # (conectado, mensagem_status)
    dados_recebidos = Signal(dict)            # pacote decodificado para displays
    leitura_para_gravar = Signal(dict)        # leitura válida para histórico/banco
    erro_serial = Signal(str)                 # falhas de porta, handshake ou protocolo

    def __init__(
        self,
        porta: str,
        baud_rate: int = 9600,
        timeout: float = 1.0,
        simular_sem_hardware: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.porta = porta
        self.baud_rate = int(baud_rate)
        self.timeout = float(timeout)
        self.simular_sem_hardware = simular_sem_hardware

        self._executando = False
        self._serial_conn = None

    def _realizar_handshake(self) -> bool:
        """Executa o ciclo inicial de handshake com a placa externa."""
        if self.simular_sem_hardware or self._serial_conn is None:
            time.sleep(0.15)
            return True

        try:
            self._serial_conn.reset_input_buffer()
            self._serial_conn.write(b"HELLO\n")
            self._serial_conn.flush()

            resposta = self._serial_conn.readline().decode("utf-8", errors="ignore").strip()
            # Aceita resposta explícita de handshake ou prossegue se a placa já transmite telemetria
            if resposta in ("ACK", "READY", "OK") or resposta.startswith("{"):
                return True
            if not resposta:
                raise TimeoutError("Sem resposta de handshake da placa.")
            return True
        except Exception as exc:
            self.erro_serial.emit(f"Falha no handshake ({self.porta}): {exc}")
            return False

    def _decodificar_pacote(self, linha: str) -> dict | None:
        """
        Valida e converte um pacote bruto em dicionário normalizado.
        Suporta JSON (ex.: {"tensao": 220.4, "corrente": 12.8}) ou CSV (ex.: 220.4,12.8).
        """
        texto = linha.strip()
        if not texto:
            return None

        try:
            if texto.startswith("{"):
                payload = json.loads(texto)
                tensao = float(payload["tensao"])
                corrente = float(payload["corrente"])
            else:
                partes = [p.strip() for p in texto.split(",")]
                if len(partes) < 2:
                    return None
                tensao = float(partes[0])
                corrente = float(partes[1])

            return {
                "tensao": tensao,
                "corrente": corrente,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            logging.warning("Pacote serial inválido ignorado ('%s'): %s", texto, exc)
            return None

    def run(self):
        self._executando = True

        if not self.simular_sem_hardware:
            if serial is None:
                self.erro_serial.emit("Biblioteca 'pyserial' não instalada.")
                self.conexao_alterada.emit(False, "Erro: pyserial ausente")
                return

            try:
                self._serial_conn = serial.Serial(
                    port=self.porta,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                )
            except Exception as exc:
                self.erro_serial.emit(f"Não foi possível abrir {self.porta}: {exc}")
                self.conexao_alterada.emit(False, f"Falha ao abrir {self.porta}")
                return

        if not self._realizar_handshake():
            self._fechar_porta()
            self.conexao_alterada.emit(False, "Falha no handshake")
            return

        self.conexao_alterada.emit(
            True, f"Conectado ({self.porta} @ {self.baud_rate} bps)"
        )

        passo = 0
        while self._executando:
            try:
                if self.simular_sem_hardware:
                    # Simulação contínua sem bloquear a main thread
                    passo += 1
                    tensao_sim = round(220.0 + (passo % 5) * 0.4, 2)
                    corrente_sim = round(10.0 + (passo % 7) * 1.2, 2)
                    pacote = {
                        "tensao": tensao_sim,
                        "corrente": corrente_sim,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    self.dados_recebidos.emit(pacote)
                    self.leitura_para_gravar.emit(pacote)
                    self.msleep(1000)
                else:
                    if self._serial_conn and self._serial_conn.in_waiting > 0:
                        raw = self._serial_conn.readline()
                        linha = raw.decode("utf-8", errors="ignore")
                        pacote = self._decodificar_pacote(linha)
                        if pacote:
                            self.dados_recebidos.emit(pacote)
                            self.leitura_para_gravar.emit(pacote)
                    else:
                        self.msleep(20)
            except Exception as exc:
                if self._executando:
                    logging.exception("Erro durante leitura contínua na porta serial.")
                    self.erro_serial.emit(f"Erro de comunicação em {self.porta}: {exc}")
                break

        self._fechar_porta()
        self.conexao_alterada.emit(False, "Desconectado")

    def parar(self):
        """Solicita encerramento seguro da thread worker."""
        self._executando = False
        self.wait(2000)

    def _fechar_porta(self):
        if self._serial_conn is not None:
            try:
                if self._serial_conn.is_open:
                    self._serial_conn.close()
            except Exception:
                logging.exception("Erro ao fechar porta serial.")
            finally:
                self._serial_conn = None