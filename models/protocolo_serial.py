import time

def validar_pacote(linha: str) -> tuple[bool, str | None]:
    """
    Valida um pacote serial no formato $DAT,...*XX
    Retorna uma tupla (sucesso: bool, payload: str)
    """
    linha = linha.strip()

    if not linha.startswith('$') or '*' not in linha:
        return False, None

    try:
        payload, checksum_recebido = linha[1:].split('*', 1)
    except ValueError:
        return False, None

    checksum_calculado = 0
    for caractere in payload:
        checksum_calculado ^= ord(caractere)

    checksum_formatado = f"{checksum_calculado:02X}"

    if checksum_formatado == checksum_recebido.upper():
        return True, payload
    return False, None


def decodificar_telemetria(linha: str) -> dict | None:
    """
    Valida o checksum XOR e converte o payload '$DAT,v_raw,i_raw,d1,d2*XX'
    em valores de engenharia.
    """
    valido, payload = validar_pacote(linha)
    if not valido or not payload:
        return None

    partes = [p.strip() for p in payload.split(',')]
    if len(partes) < 5 or partes[0] != "DAT":
        return None

    try:
        raw_tensao = float(partes[1])
        raw_corrente = float(partes[2])

        tensao = round((raw_tensao / 1023.0) * 250.0, 2)
        corrente = round((raw_corrente / 1023.0) * 30.0, 2)
        potencia = round(tensao * corrente, 2)

        # Campos 3 e 4 do pacote conforme o protocolo oficial da placa:
        # <STATUS_RELE> (estado real do relé/carga) e <STATUS_BOTAO>.
        status_rele = int(partes[3]) == 1
        status_botao = int(partes[4]) == 1

        return {
            "tensao": tensao,
            "corrente": corrente,
            "potencia": potencia,
            "status_rele": status_rele,
            "status_botao": status_botao,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except (ValueError, IndexError):
        return None
