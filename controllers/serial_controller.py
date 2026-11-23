from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog

from controllers.serial_worker import SerialWorker
from models.config_manager import carregar_ou_criar_config, salvar_config
from ui.serial_config_dialog import Ui_DialogSerial


class SerialConfigController(QDialog):
    """
    Controller da tela de Configuração da Comunicação Serial.
    Inicia/encerra a SerialWorker (QThread) e notifica o controller principal.
    """

    status_alterado = Signal(bool, dict)
    worker_iniciado = Signal(object)
    worker_encerrado = Signal()

    def __init__(
        self,
        parent=None,
        worker_ativo: SerialWorker | None = None,
        simular_sem_hardware: bool = False,
    ):
        super().__init__(parent)

        self.ui = Ui_DialogSerial()
        self.ui.setupUi(self)

        self.simular_sem_hardware = simular_sem_hardware
        self.worker: SerialWorker | None = worker_ativo
        self.conectado = bool(worker_ativo is not None and worker_ativo.isRunning())

        self.carregar_configuracoes()

        if self.conectado and self.worker is not None:
            self._definir_controles_ativos(True)
            self.ui.lblStatusValor.setText(
                f"Conectado ({self.worker.porta} @ {self.worker.baud_rate} bps)"
            )
            self.ui.lblStatusValor.setStyleSheet("color: #27ae60; font-weight: bold;")
            # Reconecta aos sinais da worker já em execução para que esta janela
            # (reaberta) continue refletindo o estado real da conexão.
            self.worker.conexao_alterada.connect(self._on_conexao_alterada)
            self.worker.erro_serial.connect(self._on_erro_serial)
            self.worker.finished.connect(self._on_worker_finalizado)
        else:
            self._definir_controles_ativos(False)

        self.ui.btnConectar.clicked.connect(self.conectar)
        self.ui.btnDesconectar.clicked.connect(self.desconectar)

    def carregar_configuracoes(self):
        config = carregar_ou_criar_config()

        if hasattr(self.ui, "cbPortaCom"):
            porta_salva = config.get("porta_com", "COM3")
            index_porta = self.ui.cbPortaCom.findText(porta_salva)
            if index_porta >= 0:
                self.ui.cbPortaCom.setCurrentIndex(index_porta)

        if hasattr(self.ui, "cbBaudRate"):
            baud_salvo = str(config.get("baud_rate", 9600))
            index_baud = self.ui.cbBaudRate.findText(baud_salvo)
            if index_baud >= 0:
                self.ui.cbBaudRate.setCurrentIndex(index_baud)

    def _dados_conexao(self) -> dict:
        return {
            "porta": self.ui.cbPortaCom.currentText(),
            "baud_rate": self.ui.cbBaudRate.currentText(),
            "timeout": self.ui.spinTimeout.value(),
        }

    def _definir_controles_ativos(self, conectado: bool):
        self.conectado = conectado
        self.ui.btnConectar.setEnabled(not conectado)
        self.ui.btnDesconectar.setEnabled(conectado)
        self.ui.cbPortaCom.setEnabled(not conectado)
        self.ui.cbBaudRate.setEnabled(not conectado)
        self.ui.spinTimeout.setEnabled(not conectado)

    def conectar(self):
        if self.conectado or (self.worker is not None and self.worker.isRunning()):
            return

        dados = self._dados_conexao()

        config_atual = carregar_ou_criar_config()
        try:
            baud_int = int(dados["baud_rate"])
        except (TypeError, ValueError):
            baud_int = int(config_atual.get("baud_rate", 9600))

        taxa_amostragem = config_atual.get("taxa_amostragem_ms", 1000)
        config_atual["porta_com"] = dados["porta"]
        config_atual["baud_rate"] = baud_int
        config_atual["taxa_amostragem_ms"] = taxa_amostragem
        dados["taxa_amostragem_ms"] = taxa_amostragem
        salvar_config(config_atual)

        self.ui.lblStatusValor.setText(
            f"Conectando ({dados['porta']} @ {baud_int} bps)..."
        )
        self.ui.lblStatusValor.setStyleSheet("color: #d68910; font-weight: bold;")
        self.ui.btnConectar.setEnabled(False)

        # parent=None evita que o worker seja destruído ao fechar este QDialog
        self.worker = SerialWorker(
            porta=dados["porta"],
            baud_rate=baud_int,
            timeout=float(dados["timeout"]),
            simular_sem_hardware=self.simular_sem_hardware,
            taxa_amostragem_ms=int(taxa_amostragem),
            parent=None,
        )
        self.worker.conexao_alterada.connect(self._on_conexao_alterada)
        self.worker.erro_serial.connect(self._on_erro_serial)
        self.worker.finished.connect(self._on_worker_finalizado)

        self.worker_iniciado.emit(self.worker)
        self.worker.start()

    def desconectar(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.parar()

    def _on_conexao_alterada(self, conectado: bool, mensagem: str):
        dados = self._dados_conexao()
        self._definir_controles_ativos(conectado)

        self.ui.lblStatusValor.setText(mensagem)
        if conectado:
            self.ui.lblStatusValor.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.ui.lblStatusValor.setStyleSheet("color: #c0392b; font-weight: bold;")
            self.worker_encerrado.emit()

        self.status_alterado.emit(conectado, dados)

    def _on_erro_serial(self, mensagem: str):
        # O aviso ao usuário é responsabilidade da janela principal (persistente),
        # que permanece escutando a worker mesmo com este diálogo fechado.
        # Aqui apenas refletimos o estado desconectado nesta tela.
        self._definir_controles_ativos(False)
        self.ui.lblStatusValor.setText(f"Desconectado: {mensagem}")
        self.ui.lblStatusValor.setStyleSheet("color: #c0392b; font-weight: bold;")
        self.worker_encerrado.emit()

    def _on_worker_finalizado(self):
        self.worker = None
