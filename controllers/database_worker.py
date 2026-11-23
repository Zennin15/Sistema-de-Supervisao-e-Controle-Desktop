import logging
import queue
import sqlite3
from PySide6.QtCore import QThread, Signal

from logs.logger import registrar_erro_emergencia
from models.repository import (
    ActuatorRepository,
    LimitRepository,
    Repository,
    TAG_DISJUNTOR_PRINCIPAL,
)

class DatabaseWorker(QThread):
    """
    QThread dedicada à persistência e consultas SQLite:
    - Isola escritas e queries volumosas da Main Thread (GUI)
    - Processa comandos sequencialmente via fila thread-safe para evitar 'database is locked'
    - Emite sinais com resultados/erros para a interface
    """

    historico_carregado = Signal(list)
    atuadores_carregados = Signal(list)
    limites_carregados = Signal(list)
    evento_gravado = Signal(str, str, object)          # (tipo_evento, descricao, valor_medido)
    status_atuador_alterado = Signal(str, str)        # (tag, novo_status)
    limites_gravados = Signal(list)
    erro_persistencia = Signal(str, str)              # (titulo, mensagem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fila = queue.Queue()
        self._executando = True
        self._parar_sentinel = object()

    def _enfileirar(self, comando: str, payload=None):
        if not self._executando:
            return
        self._fila.put((comando, payload))

    # --- API pública de comandos (chamada por Controllers / SerialWorker) ---

    def solicitar_historico(self):
        self._enfileirar("listar_historico")

    def solicitar_atuadores(self):
        self._enfileirar("listar_atuadores")

    def solicitar_limites(self):
        self._enfileirar("listar_limites")

    def gravar_evento(self, tipo_evento: str, descricao: str, valor_medido=None, tag_atuador: str = TAG_DISJUNTOR_PRINCIPAL):
        self._enfileirar(
            "gravar_evento",
            {
                "tipo_evento": tipo_evento,
                "descricao": descricao,
                "valor_medido": valor_medido,
                "tag_atuador": tag_atuador,
            },
        )

    def gravar_leitura_telemetria(self, pacote: dict):
        """
        Recebe uma amostra decodificada (ex.: {'tensao': 220.4, 'corrente': 12.8})
        e grava o registro de telemetria em segundo plano.
        """
        self._enfileirar("gravar_telemetria", pacote)

    def registrar_acao_disjuntor(self, tag: str, novo_status: str, motivo: str = "", valor_medido=None):
        """
        Atualiza o estado do atuador e registra o evento no histórico
        na mesma transação em segundo plano.
        """
        self._enfileirar(
            "acao_disjuntor",
            {
                "tag": tag,
                "novo_status": novo_status,
                "motivo": motivo,
                "valor_medido": valor_medido,
            },
        )

    def substituir_limites(self, limites: list):
        self._enfileirar("substituir_limites", limites)

    # --- Loop da QThread ---

    def run(self):
        self._executando = True

        while self._executando:
            item = self._fila.get()
            if item is self._parar_sentinel:
                self._fila.task_done()
                break

            comando, payload = item
            try:
                self._executar_comando(comando, payload)
            except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
                logging.exception("Erro no DatabaseWorker ao executar '%s'.", comando)
                if comando == "acao_disjuntor" and isinstance(payload, dict) and "EMERG" in str(payload.get("tag", "")).upper():
                    registrar_erro_emergencia(str(exc))
                self.erro_persistencia.emit(
                    "Erro de Banco de Dados",
                    f"Falha ao executar '{comando}':\n{exc}",
                )
            finally:
                self._fila.task_done()

    def _executar_comando(self, comando: str, payload):
        if comando == "listar_historico":
            eventos = Repository.listar_todos()
            self.historico_carregado.emit(eventos)

        elif comando == "listar_atuadores":
            atuadores = ActuatorRepository.listar_todos()
            self.atuadores_carregados.emit(atuadores)

        elif comando == "listar_limites":
            limites = LimitRepository.listar_todos()
            self.limites_carregados.emit(limites)

        elif comando == "gravar_evento":
            atuador_id = ActuatorRepository.obter_id_por_tag(payload["tag_atuador"])
            Repository.registrar_evento(
                tipo_evento=payload["tipo_evento"],
                descricao=payload["descricao"],
                valor_medido=payload["valor_medido"],
                atuador_id=atuador_id,
            )
            self.evento_gravado.emit(
                payload["tipo_evento"],
                payload["descricao"],
                payload["valor_medido"],
            )
            self.historico_carregado.emit(Repository.listar_todos())

        elif comando == "gravar_telemetria":
            tensao = payload.get("tensao")
            corrente = payload.get("corrente")
            atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            descricao = f"Tensão={tensao} V, Corrente={corrente} A"
            Repository.registrar_evento(
                tipo_evento="Telemetria",
                descricao=descricao,
                valor_medido=corrente,
                atuador_id=atuador_id,
            )
            self.evento_gravado.emit("Telemetria", descricao, corrente)

        elif comando == "acao_disjuntor":
            from database.connection import Database

            tag = payload["tag"]
            novo_status = payload["novo_status"]
            motivo = payload.get("motivo") or f"Estado alterado para {novo_status}"
            valor_medido = payload.get("valor_medido")

            conn = Database.get_connection()
            try:
                with conn:
                    ActuatorRepository.atualizar_status_por_tag(conn, tag, novo_status)
                    atuador_id = ActuatorRepository.obter_id_por_tag(tag, conn)
                    Repository.inserir_em_conexao(
                        conn,
                        tipo_evento="Atuador",
                        descricao=f"{tag}: {motivo}",
                        valor_medido=valor_medido,
                        atuador_id=atuador_id,
                    )
            finally:
                conn.close()

            self.status_atuador_alterado.emit(tag, novo_status)
            self.historico_carregado.emit(Repository.listar_todos())

        elif comando == "substituir_limites":
            LimitRepository.substituir_todos(payload)
            self.limites_gravados.emit(payload)

    def parar(self, aguardar_ms: int = 3000):
        """Encerra a worker thread com segurança após drenar ou interromper o loop."""
        self._executando = False
        self._fila.put(self._parar_sentinel)
        self.wait(aguardar_ms)