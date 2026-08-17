import sys
from PySide6.QtWidgets import QApplication
from controller.main_window_controller import MainWindowController

def main():         
    # Inicia o motor do Qt
    app = QApplication(sys.argv)
    
    # Cria e exibe a janela principal
    janela_principal = MainWindowController()
    janela_principal.show()
    
    # Mantém o programa rodando até o usuário fechar
    sys.exit(app.exec())

if __name__ == "__main__": 
    main()