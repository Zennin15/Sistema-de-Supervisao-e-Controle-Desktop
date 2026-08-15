from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem, QMessageBox
from ui.limits_configuration_window import Ui_Dialog

class LimitConfigurationController(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Tensão", "Corrente"])

        self.ui.botaoAdicionarLimite.clicked.connect(self.new_row)
        self.ui.botaoRemoverLimite.clicked.connect(self.remove_row)

        self.ui.botaoAplicarLimite.clicked.connect(self.validar_e_aplicar)
        self.ui.botaoCancelarLimite.clicked.connect(self.reject)

    # Faz a varredura na tabela quando o usuário clica em Aplicar
    def validar_e_aplicar(self):
        # Verifica se há pelo menos uma linha
        if self.ui.tableWidget.rowCount() == 0:
            QMessageBox.information(self, "Aviso", "Adicione pelo menos uma regra de limite.")
            return

        for row in range(self.ui.tableWidget.rowCount()):
            item_tensao = self.ui.tableWidget.item(row, 0)
            item_corrente = self.ui.tableWidget.item(row, 1)

            tensao = item_tensao.text().strip() if item_tensao else ""
            corrente = item_corrente.text().strip() if item_corrente else ""

            # Se a linha inteira estiver vazia, podemos ignorá-la ou excluí-la
            if tensao == "" and corrente == "":
                continue

            # Valida cada célula individualmente (passando contexto para a mensagem)
            if not self.validar_celula(tensao, "Tensão", row):
                return  # Interrompe a função, a janela nao fecha
            
            if not self.validar_celula(corrente, "Corrente", row):
                return  # Interrompe a função, a janela não fecha

        self.accept()

    def validar_celula(self, texto, nome_coluna, linha):
        if texto == "":
            QMessageBox.warning(self, "Campo Vazio", f"Por favor, preencha o limite de {nome_coluna} na linha {linha + 1}.")
            return False
    
        try:
            float(texto)
            return True 
        
        except ValueError:
            QMessageBox.critical(self, "Entrada Inválida", f"O valor '{texto}' na linha {linha + 1} não é um número válido.")
            return False

    def carregar_dados(self, dados_salvos):
        self.ui.tableWidget.setRowCount(0) 

        for limite in dados_salvos:
            current_rows = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(current_rows)
            
            self.ui.tableWidget.setItem(current_rows, 0, QTableWidgetItem(limite["Tensao"]))
            self.ui.tableWidget.setItem(current_rows, 1, QTableWidgetItem(limite["Corrente"]))

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
