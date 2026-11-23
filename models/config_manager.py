import copy
import json
import os

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "porta_com": "COM3",
    "baud_rate": 9600,
    "taxa_amostragem_ms": 1000,
    "limites_alerta": {
        "tensao_minima": 180.0,
        "tensao_maxima": 240.0,
        "corrente_maxima": 25.0,
    },
}


def _mesclar_com_padrao(padrao: dict, carregado: dict) -> dict:
    resultado = copy.deepcopy(padrao)
    if not isinstance(carregado, dict):
        return resultado

    for chave, valor in carregado.items():
        if (
            chave in resultado
            and isinstance(resultado[chave], dict)
            and isinstance(valor, dict)
        ):
            resultado[chave] = _mesclar_com_padrao(resultado[chave], valor)
        elif chave in resultado:
            resultado[chave] = valor

    return resultado


def salvar_config(novos_dados: dict) -> dict:
    """Atualiza e salva os parâmetros operacionais no arquivo data/config.json."""
    config_normalizada = _mesclar_com_padrao(DEFAULT_CONFIG, novos_dados or {})
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_normalizada, f, indent=4, ensure_ascii=False)
        print(f"Arquivo '{CONFIG_FILE}' atualizado e salvo com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo {CONFIG_FILE}: {e}")
    return config_normalizada


def carregar_ou_criar_config() -> dict:
    """
    Valida se o arquivo config.json existe.
    Caso não exista (ou esteja corrompido/inválido), recria-o automaticamente
    com valores padrão seguros e retorna o dicionário normalizado.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Arquivo '{CONFIG_FILE}' não encontrado. Criando com valores padrão.")
        return salvar_config(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        config_normalizada = _mesclar_com_padrao(DEFAULT_CONFIG, config)
        print(f"Arquivo '{CONFIG_FILE}' carregado com sucesso.")
        return config_normalizada
    except Exception as e:
        print(f"Erro ao ler o arquivo {CONFIG_FILE}: {e}. Recriando com valores padrão.")
        return salvar_config(DEFAULT_CONFIG)
