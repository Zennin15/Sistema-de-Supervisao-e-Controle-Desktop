from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal
from ui.config_dialog import Ui_Dialog

class ConfigDialogController(QDialog):
    # Sinal personalizado para enviar as regras para a janela principal
    regras_salvas = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Instancia a interface gerada a partir do config_dialog.ui
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Conecta os botões padrão (OK / Cancelar) do modal
        if hasattr(self.ui, 'buttonBox'):
            self.ui.buttonBox.accepted.connect(self.salvar_regras)
            self.ui.buttonBox.rejected.connect(self.reject)

    def salvar_regras(self):
        try:
            # Tenta ler os componentes pelos nomes atribuídos na UI
            spin_corrente = getattr(self.ui, 'spinCorrente', None) or getattr(self.ui, 'inputCorrente', None) or getattr(self.ui, 'doubleSpinBox', None)
            spin_tensao = getattr(self.ui, 'spinTensao', None) or getattr(self.ui, 'inputTensao', None) or getattr(self.ui, 'doubleSpinBox_2', None)

            if not spin_corrente or not spin_tensao:
                QMessageBox.critical(self, "Erro", "Campos de entrada não foram encontrados na interface.")
                return

            limite_corrente = float(spin_corrente.value())
            limite_tensao = float(spin_tensao.value())

            if limite_corrente <= 0 or limite_tensao <= 0:
                QMessageBox.warning(self, "Aviso de Validação", "Os limites devem ser maiores que zero.")
                return

            dados_regras = {
                "corrente_max": limite_corrente,
                "tensao_max": limite_tensao
            }

            self.regras_salvas.emit(dados_regras)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro de Entrada", f"Insira valores numéricos válidos. Detalhes: {e}")