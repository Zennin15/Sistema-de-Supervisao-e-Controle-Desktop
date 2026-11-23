import logging

# Configuração do subsistema de auditoria e diagnóstico (smartgrid.log)
logging.basicConfig(
    filename="smartgrid.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8"
)

def registrar_log_inicializacao():
    # [INFO] Conexão com SQLite estabelecida e esquema validado.
    logging.info("Conexão com SQLite estabelecida e esquema validado.")

def registrar_alerta_corrente(corrente_atual, limite):
    # [WARNING] Limite de corrente violado: 28.5A (Limite configurado: 25.0A).
    logging.warning(f"Limite de corrente violado: {corrente_atual}A (Limite configurado: {limite}A).")

def registrar_erro_emergencia(motivo):
    # [ERROR] Falha na operação de corte emergencial. Rollback executado: <motivo>.
    logging.error(f"Falha na operação de corte emergencial. Rollback executado: {motivo}.")
