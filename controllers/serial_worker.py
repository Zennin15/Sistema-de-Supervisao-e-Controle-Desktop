import logging
import time
from PySide6.QtCore import QThread, Signal
from models.protocolo_serial import decodificar_telemetria

try:
    import serial
except ImportError:
    serial = None

class SerialWorker(QThread):
    conexao_alterada = Signal(bool, str)
    dados_recebidos = Signal(dict)
    leitura_para_gravar = Signal(dict)
    erro_serial = Signal(str)
    comando_enviado = Signal(str)

    TAXAS_SUPORTADAS = (9600, 19200, 38400, 115200)

    def __init__(
        self,
        porta: str,
        baud_rate: int = 9600,
        timeout: float = 1.0,
        simular_sem_hardware: bool = False,
        taxa_amostragem_ms: int = 1000,
        parent=None,
    ):
        super().__init__(parent)
        self.porta = porta
        self.baud_rate = int(baud_rate) if int(baud_rate) in self.TAXAS_SUPORTADAS else 9600
        self.timeout = float(timeout)
        self.simular_sem_hardware = simular_sem_hardware
        # A placa real transmite a 200 Hz (a cada 5ms) - gravar cada pacote no
        # SQLite seria inviável (cada INSERT abre/fecha conexão e dá commit).
        # Por isso só repassamos 1 leitura para persistência a cada
        # taxa_amostragem_ms; o restante dos pacotes ainda atualiza o
        # dashboard normalmente, só não vira registro de histórico.
        self._taxa_amostragem_ms = max(100, int(taxa_amostragem_ms))
        self._executando = False
        self._serial_conn = None
        self._comando_pendente: str | None = None
        self._ultimo_registro_gravacao = 0.0

    def _realizar_handshake(self) -> bool:
        if self.simular_sem_hardware or self._serial_conn is None:
            time.sleep(0.1)
            return True

        try:
            if not self._serial_conn.is_open:
                self._serial_conn.baudrate = 9600
                self._serial_conn.open()
            elif self._serial_conn.baudrate != 9600:
                self._serial_conn.baudrate = 9600

            time.sleep(1.5)
            self._serial_conn.reset_input_buffer()

            comando = f"!S{self.baud_rate}\r\n".encode("ascii")
            ack_recebido = False

            for tentativa in range(2):
                self._serial_conn.write(comando)
                self._serial_conn.flush()

                limite = time.monotonic() + 1.2
                while time.monotonic() < limite:
                    bruto = self._serial_conn.readline()
                    if not bruto:
                        continue
                    texto = bruto.decode("ascii", errors="ignore").strip()
                    if "ACK:" in texto or texto.startswith("$DAT,"):
                        ack_recebido = True
                        break

                if ack_recebido:
                    break
                if tentativa == 0:
                    time.sleep(0.3)

            if not ack_recebido:
                raise TimeoutError("Placa nao confirmou o comando !S.")

            if self.baud_rate != 9600:
                time.sleep(0.05)
                # Reabrir a porta reseta o Uno (DTR); só troca a taxa.
                self._serial_conn.baudrate = self.baud_rate
                self._serial_conn.reset_input_buffer()

            return True
        except Exception as exc:
            self.erro_serial.emit(f"Falha no handshake ({self.porta}): {exc}")
            return False

    def solicitar_corte(self, abrir: bool):
        """Solicita à placa que corte (desligue o relé) ou restabeleça
        (ligue o relé) a carga, conforme o protocolo oficial: '!0' desliga
        o relé (corte) e '!1' liga o relé (restabelece).

        Thread-safe por design: apenas marca o comando pendente (atribuição
        simples, atômica no CPython); o envio real acontece dentro do loop
        desta própria worker, na mesma thread que já controla a porta serial.
        """
        self._comando_pendente = "!0\r\n" if abrir else "!1\r\n"

    def _processar_comando_pendente(self):
        comando = self._comando_pendente
        if comando is None:
            return
        self._comando_pendente = None

        if self.simular_sem_hardware:
            logging.info("Comando simulado enviado a placa: %s", comando.strip())
            self.comando_enviado.emit(comando.strip())
            return

        if self._serial_conn is None:
            self.erro_serial.emit(
                f"Comando {comando.strip()} nao enviado: porta {self.porta} nao esta aberta."
            )
            return

        try:
            n = self._serial_conn.write(comando.encode("ascii"))
            self._serial_conn.flush()
            logging.info(
                "Comando '%s' escrito em %s (%s bytes).", comando.strip(), self.porta, n
            )
            self.comando_enviado.emit(comando.strip())
        except Exception as exc:
            self.erro_serial.emit(
                f"Falha ao enviar comando de corte para {self.porta}: {exc}"
            )

    def _repassar_para_gravacao(self, pacote: dict):
        """Limita a persistência a 1 leitura a cada taxa_amostragem_ms,
        mesmo que a placa envie pacotes muito mais rápido (200 Hz real)."""
        agora = time.monotonic()
        if (agora - self._ultimo_registro_gravacao) * 1000.0 >= self._taxa_amostragem_ms:
            self._ultimo_registro_gravacao = agora
            self.leitura_para_gravar.emit(pacote)

    def run(self):
        self._executando = True

        if not self.simular_sem_hardware:
            if serial is None:
                self.erro_serial.emit("Biblioteca 'pyserial' nao instalada.")
                self.conexao_alterada.emit(False, "Erro: pyserial ausente")
                return

            try:
                self._serial_conn = serial.Serial(
                    port=self.porta,
                    baudrate=9600,
                    timeout=self.timeout,
                )
            except Exception as exc:
                self.erro_serial.emit(f"Nao foi possivel abrir {self.porta}: {exc}")
                self.conexao_alterada.emit(False, f"Falha ao abrir {self.porta}")
                return

        if not self._realizar_handshake():
            self._fechar_porta()
            self.conexao_alterada.emit(False, "Falha no handshake")
            return

        self.conexao_alterada.emit(True, f"Conectado ({self.porta} @ {self.baud_rate} bps)")

        passo = 0
        while self._executando:
            try:
                self._processar_comando_pendente()

                if self.simular_sem_hardware:
                    passo += 1
                    v_adc = 512 + (passo % 15)
                    i_adc = 340 + (passo % 10)
                    payload_sim = f"DAT,{v_adc},{i_adc},1,0"
                    cs = 0
                    for c in payload_sim:
                        cs ^= ord(c)
                    linha_sim = f"${payload_sim}*{cs:02X}\r\n"

                    pacote = decodificar_telemetria(linha_sim)
                    if pacote:
                        self.dados_recebidos.emit(pacote)
                        self._repassar_para_gravacao(pacote)
                    self.msleep(1000)
                else:
                    if self._serial_conn and self._serial_conn.in_waiting > 0:
                        raw = self._serial_conn.readline()
                        linha = raw.decode("ascii", errors="ignore")
                        pacote = decodificar_telemetria(linha)
                        if pacote:
                            self.dados_recebidos.emit(pacote)
                            self._repassar_para_gravacao(pacote)
                    else:
                        self.msleep(20)
            except Exception as exc:
                if self._executando:
                    self.erro_serial.emit(f"Erro de comunicacao em {self.porta}: {exc}")
                break

        self._fechar_porta()
        self.conexao_alterada.emit(False, "Desconectado")

    def parar(self):
        self._executando = False
        self.wait(2000)

    def _fechar_porta(self):
        if self._serial_conn is not None:
            try:
                if self._serial_conn.is_open:
                    self._serial_conn.write(b"!P\r\n")
                    self._serial_conn.flush()
                    time.sleep(0.03)
                    self._serial_conn.close()
            except Exception:
                pass
            finally:
                self._serial_conn = None
