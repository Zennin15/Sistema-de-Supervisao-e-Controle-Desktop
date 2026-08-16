from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal, QFile
from PySide6.QtUiTools import QUiLoader

class ConfigDialogController(QDialog):
    # Sinal personalizado para enviar as regras para a janela principal
    regras_salvas = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Carrega a interface gráfica do arquivo .ui
        loader = QUiLoader()
        ui_file = QFile("ui/config_dialog.ui")
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # Conecta os botões padrão (OK / Cancelar) do modal
        if hasattr(self.ui, 'buttonBox'):
            self.ui.buttonBox.accepted.connect(self.salvar_regras)
            self.ui.buttonBox.rejected.connect(self.reject)

    def salvar_regras(self):
        try:
            # Resgata os valores informados nos campos
            limite_corrente = float(self.ui.inputCorrente.value() if hasattr(self.ui.inputCorrente, 'value') else self.ui.inputCorrente.text())
            limite_tensao = float(self.ui.inputTensao.value() if hasattr(self.ui.inputTensao, 'value') else self.ui.inputTensao.text())

            # Validação: os limites devem ser positivos
            if limite_corrente <= 0 or limite_tensao <= 0:
                QMessageBox.warning(self, "Aviso de Validação", "Os limites devem ser maiores que zero.")
                return

            dados_regras = {
                "corrente_max": limite_corrente,
                "tensao_max": limite_tensao
            }

            # Emite o sinal com os dados e fecha o modal
            self.regras_salvas.emit(dados_regras)
            self.accept()

        except ValueError:
            QMessageBox.critical(self, "Erro de Entrada", "Insira valores numéricos válidos.")