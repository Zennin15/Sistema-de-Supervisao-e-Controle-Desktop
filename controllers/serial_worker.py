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

    TAXAS_SUPORTADAS = (9600, 19200, 38400, 115200)

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
        self.baud_rate = int(baud_rate) if int(baud_rate) in self.TAXAS_SUPORTADAS else 9600
        self.timeout = float(timeout)
        self.simular_sem_hardware = simular_sem_hardware
        self._executando = False
        self._serial_conn = None

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
                self._serial_conn.close()
                time.sleep(0.05)
                self._serial_conn.baudrate = self.baud_rate
                self._serial_conn.open()
                self._serial_conn.reset_input_buffer()

            return True
        except Exception as exc:
            self.erro_serial.emit(f"Falha no handshake ({self.porta}): {exc}")
            return False

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
                        self.leitura_para_gravar.emit(pacote)
                    self.msleep(1000)
                else:
                    if self._serial_conn and self._serial_conn.in_waiting > 0:
                        raw = self._serial_conn.readline()
                        linha = raw.decode("ascii", errors="ignore")
                        pacote = decodificar_telemetria(linha)
                        if pacote:
                            self.dados_recebidos.emit(pacote)
                            self.leitura_para_gravar.emit(pacote)
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
