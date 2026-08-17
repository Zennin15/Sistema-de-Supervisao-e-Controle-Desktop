from PySide6.QtWidgets import QDialog, QMessageBox, QTableWidgetItem
from PySide6.QtCore import Signal
from ui.limits_configuration_window import Ui_Dialog

class LimitsConfigurationWindowController(QDialog):
    # Sinal personalizado para enviar a lista de limites salvos para a tela principal
    regras_salvas = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Configura as colunas da tabela de limites
        if hasattr(self.ui, 'tableWidget'):
            self.ui.tableWidget.setColumnCount(2)
            self.ui.tableWidget.setHorizontalHeaderLabels(["Tensão", "Corrente"])

        # Conecta os botões da interface
        if hasattr(self.ui, 'botaoAdicionarLimite'):
            self.ui.botaoAdicionarLimite.clicked.connect(self.new_row)
        if hasattr(self.ui, 'botaoRemoverLimite'):
            self.ui.botaoRemoverLimite.clicked.connect(self.remove_row)
        if hasattr(self.ui, 'botaoAplicarLimite'):
            self.ui.botaoAplicarLimite.clicked.connect(self.validar_e_aplicar)
        if hasattr(self.ui, 'botaoCancelarLimite'):
            self.ui.botaoCancelarLimite.clicked.connect(self.reject)

    def validar_e_aplicar(self):
        """Faz a varredura e validação na tabela quando o usuário clica em Aplicar."""
        if self.ui.tableWidget.rowCount() == 0:
            QMessageBox.information(self, "Aviso", "Adicione pelo menos uma regra de limite.")
            return

        for row in range(self.ui.tableWidget.rowCount()):
            item_tensao = self.ui.tableWidget.item(row, 0)
            item_corrente = self.ui.tableWidget.item(row, 1)

            tensao = item_tensao.text().strip() if item_tensao else ""
            corrente = item_corrente.text().strip() if item_corrente else ""

            # Se a linha inteira estiver vazia, pode ignorar
            if tensao == "" and corrente == "":
                continue

            # Valida cada célula individualmente
            if not self.validar_celula(tensao, "Tensão", row):
                return
            
            if not self.validar_celula(corrente, "Corrente", row):
                return

        # Emite o sinal enviando os dados para a janela principal e fecha o modal
        dados = self.get_dados()
        self.regras_salvas.emit(dados)
        self.accept()

    def validar_celula(self, texto, nome_coluna, linha):
        if texto == "":
            QMessageBox.warning(self, "Campo Vazio", f"Por favor, preencha o limite de {nome_coluna} na linha {linha + 1}.")
            return False
    
        try:
            val = float(texto)
            if val <= 0:
                QMessageBox.warning(self, "Valor Inválido", f"O valor de {nome_coluna} na linha {linha + 1} deve ser maior que zero.")
                return False
            return True 
        
        except ValueError:
            QMessageBox.critical(self, "Entrada Inválida", f"O valor '{texto}' na linha {linha + 1} não é um número válido.")
            return False

    def carregar_dados(self, dados_salvos):
        self.ui.tableWidget.setRowCount(0) 

        for limite in dados_salvos:
            current_rows = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(current_rows)
            
            self.ui.tableWidget.setItem(current_rows, 0, QTableWidgetItem(str(limite["Tensao"])))
            self.ui.tableWidget.setItem(current_rows, 1, QTableWidgetItem(str(limite["Corrente"])))

    def new_row(self): 
        current_rows = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(current_rows)

        self.ui.tableWidget.setItem(current_rows, 0, QTableWidgetItem(""))
        self.ui.tableWidget.setItem(current_rows, 1, QTableWidgetItem(""))

    def remove_row(self):
        current_row = self.ui.tableWidget.currentRow()
        if current_row >= 0:
            self.ui.tableWidget.removeRow(current_row)

    def get_dados(self):
        limites = []
        
        for row in range(self.ui.tableWidget.rowCount()):
            item_tensao = self.ui.tableWidget.item(row, 0)
            item_corrente = self.ui.tableWidget.item(row, 1)

            tensao = item_tensao.text().strip() if item_tensao else ""
            corrente = item_corrente.text().strip() if item_corrente else ""

            if tensao and corrente:
                limites.append({
                    "Tensao": tensao,
                    "Corrente": corrente
                })

        return limites