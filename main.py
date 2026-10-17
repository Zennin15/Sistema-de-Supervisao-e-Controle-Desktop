import sys
from PySide6.QtWidgets import QApplication
from controllers.main_window_controller import MainWindowController
from database.connection import Database

def main():         
    # Inicializa o banco de dados.
    Database.init_db();

    # Inicia o motor do Qt
    app = QApplication(sys.argv)
    
    # Cria e exibe a janela principal
    janela_principal = MainWindowController()
    janela_principal.show()
    
    # Mantém o programa rodando até o usuário fechar
    sys.exit(app.exec())

if __name__ == "__main__": 
    main()