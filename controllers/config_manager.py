import os
import json

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Valores default conforme a especificação do projeto
DEFAULT_CONFIG = {
    "porta_com": "COM3",
    "baud_rate": 9600,
    "limites_alerta": {
        "corrente_maxima": 25.0
    }
}

def carregar_ou_criar_config():
    """
    Valida se o arquivo config.json existe (os.path.exists).
    Caso não exista, cria-o automaticamente com valores default.
    Se existir, carrega e retorna o conteúdo do JSON.
    """
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print(f"Arquivo '{CONFIG_FILE}' criado com sucesso com valores padrão.")
        except Exception as e:
            print(f"Erro ao criar o arquivo {CONFIG_FILE}: {e}")
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            print(f"Arquivo '{CONFIG_FILE}' carregado com sucesso.")
            return config
    except Exception as e:
        print(f"Erro ao ler o arquivo {CONFIG_FILE}: {e}. Utilizando valores padrão.")
        return DEFAULT_CONFIG

def salvar_config(novos_dados):
    """
    Atualiza e salva os novos valores (porta_com, baud_rate, etc.) 
    diretamente no arquivo config.json.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(novos_dados, f, indent=4)
        print(f"Arquivo '{CONFIG_FILE}' atualizado e salvo com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo {CONFIG_FILE}: {e}")