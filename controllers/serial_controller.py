from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal
from ui.serial_config_dialog import Ui_DialogSerial
from config_manager import carregar_ou_criar_config, salvar_config

class SerialConfigController(QDialog):
    """
    Controller da tela de Configuração da Comunicação Serial.

    Nesta etapa (A1/1) não há integração física com hardware:
    os botões "Conectar" / "Desconectar" apenas atualizam o status
    visual na tela e avisam a janela principal via sinal, para que
    o evento seja registrado no histórico.
    """

    # Emitido sempre que o status de conexão muda.
    # bool -> True (conectado) / False (desconectado)
    # dict -> {'porta': str, 'baud_rate': str, 'timeout': int}
    status_alterado = Signal(bool, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_DialogSerial()
        self.ui.setupUi(self)

        self.conectado = False

        # Carrega as configurações do config.json ao iniciar a tela
        self.carregar_configuracoes()

        self.ui.btnConectar.clicked.connect(self.conectar)
        self.ui.btnDesconectar.clicked.connect(self.desconectar)

    def carregar_configuracoes(self):
        """Lê o arquivo config.json e define os valores na interface com segurança."""
        config = carregar_ou_criar_config()
        
        # Tenta definir a Porta COM se o componente existir na UI
        if hasattr(self.ui, 'cbPortaCom'):
            porta_salva = config.get("porta_com", "COM3")
            index_porta = self.ui.cbPortaCom.findText(porta_salva)
            if index_porta >= 0:
                self.ui.cbPortaCom.setCurrentIndex(index_porta)

        # Tenta definir o Baud Rate se o componente existir na UI
        if hasattr(self.ui, 'cbBaudRate'):
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

    def conectar(self):
        """Simula a conexão: atualiza o status visual e salva no config.json."""
        if self.conectado:
            return

        dados = self._dados_conexao()
        self.conectado = True

        # Atualiza e salva automaticamente no config.json os novos valores da serial
        config_atual = carregar_ou_criar_config()
        config_atual["porta_com"] = dados["porta"]
        config_atual["baud_rate"] = int(dados["baud_rate"])
        salvar_config(config_atual)

        self.ui.lblStatusValor.setText(
            f"Conectado ({dados['porta']} @ {dados['baud_rate']} bps)"
        )
        self.ui.lblStatusValor.setStyleSheet("color: #27ae60; font-weight: bold;")

        self.ui.btnConectar.setEnabled(False)
        self.ui.btnDesconectar.setEnabled(True)
        self.ui.cbPortaCom.setEnabled(False)
        self.ui.cbBaudRate.setEnabled(False)
        self.ui.spinTimeout.setEnabled(False)

        self.status_alterado.emit(True, dados)

    def desconectar(self):
        """Simula a desconexão: apenas atualiza o status visual (sem hardware real)."""
        if not self.conectado:
            return

        dados = self._dados_conexao()
        self.conectado = False

        self.ui.lblStatusValor.setText("Desconectado")
        self.ui.lblStatusValor.setStyleSheet("color: #c0392b; font-weight: bold;")

        self.ui.btnConectar.setEnabled(True)
        self.ui.btnDesconectar.setEnabled(False)
        self.ui.cbPortaCom.setEnabled(True)
        self.ui.cbBaudRate.setEnabled(True)
        self.ui.spinTimeout.setEnabled(True)

        self.status_alterado.emit(False, dados)