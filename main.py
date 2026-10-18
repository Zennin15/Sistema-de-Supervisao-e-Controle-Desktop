import sys
from PySide6.QtWidgets import QApplication
from controllers.main_window_controller import MainWindowController
from database.connection import Database
from config_manager import carregar_ou_criar_config  # Importa a sua função

def main():         
    # Inicializa o banco de dados.
    Database.init_db()

    # --- TAREFA DA PESSOA A: Valida e carrega o config.json ---
    config = carregar_ou_criar_config()

    # Inicia o motor do Qt
    app = QApplication(sys.argv)
    
    # Cria e exibe a janela principal
    janela_principal = MainWindowController()
    janela_principal.show()
    
    # Mantém o programa rodando até o usuário fechar
    sys.exit(app.exec())

if __name__ == "__main__":    
    main()
