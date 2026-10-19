from datetime import datetime

from database.connection import Database


TAG_DISJUNTOR_PRINCIPAL = "DISJUNTOR_PRINCIPAL"
TAG_RELE_EMERGENCIA = "RELE_EMERGENCIA"
STATUS_VALIDOS = ("ABERTO", "FECHADO")


class Repository:
    """Repositório de eventos: centraliza consultas parametrizadas no historico."""

    @staticmethod
    def listar_todos():
        conn = Database.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, atuador_id, data_hora, tipo_evento, valor_medido, descricao
                FROM historico_eventos
                ORDER BY id ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def inserir_em_conexao(conn, tipo_evento, descricao, valor_medido=None, atuador_id=None):
        """Insere um evento usando a conexao de uma transação ja aberta."""
        cursor = conn.execute(
            """
            INSERT INTO historico_eventos
                (atuador_id, data_hora, tipo_evento, valor_medido, descricao)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                atuador_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                str(tipo_evento),
                valor_medido,
                str(descricao or ""),
            ),
        )
        return cursor.lastrowid

    @classmethod
    def registrar_evento(cls, tipo_evento, descricao, valor_medido=None, atuador_id=None):
        conn = Database.get_connection()
        try:
            with conn:
                return cls.inserir_em_conexao(
                    conn, tipo_evento, descricao, valor_medido, atuador_id
                )
        finally:
            conn.close()

    @staticmethod
    def buscar_por_id(evento_id):
        conn = Database.get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, atuador_id, data_hora, tipo_evento, valor_medido, descricao
                FROM historico_eventos WHERE id = ?
                """,
                (evento_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def atualizar(evento_id, tipo_evento, descricao, valor_medido=None):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE historico_eventos
                    SET tipo_evento = ?, descricao = ?, valor_medido = ?
                    WHERE id = ?
                    """,
                    (str(tipo_evento), str(descricao or ""), valor_medido, evento_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def excluir(evento_id):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM historico_eventos WHERE id = ?", (evento_id,)
                )
                return cursor.rowcount > 0
        finally:
            conn.close()


class ActuatorRepository:
    """Operações de leitura e escrita dos estados dos dispositivos."""

    @staticmethod
    def listar_todos():
        conn = Database.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, tag, tipo, status, ultima_atualizacao
                FROM atuadores ORDER BY id ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def obter_por_tag(tag, conn=None):
        conexao_propria = conn is None
        if conexao_propria:
            conn = Database.get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, tag, tipo, status, ultima_atualizacao
                FROM atuadores WHERE tag = ?
                """,
                (tag,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            if conexao_propria:
                conn.close()

    @classmethod
    def obter_id_por_tag(cls, tag, conn=None):
        atuador = cls.obter_por_tag(tag, conn)
        return atuador["id"] if atuador else None

    @staticmethod
    def atualizar_status_por_tag(conn, tag, status):
        if status not in STATUS_VALIDOS:
            raise ValueError("Status de atuador deve ser ABERTO ou FECHADO.")
        cursor = conn.execute(
            """
            UPDATE atuadores
            SET status = ?, ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE tag = ?
            """,
            (status, tag),
        )
        if cursor.rowcount != 1:
            raise ValueError(f"Atuador nao encontrado: {tag}")

    @staticmethod
    def criar(tag, tipo, status="FECHADO"):
        if status not in STATUS_VALIDOS:
            raise ValueError("Status de atuador deve ser ABERTO ou FECHADO.")
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO atuadores (tag, tipo, status, ultima_atualizacao)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (tag, tipo, status),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def atualizar(atuador_id, tag, tipo, status):
        if status not in STATUS_VALIDOS:
            raise ValueError("Status de atuador deve ser ABERTO ou FECHADO.")
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE atuadores
                    SET tag = ?, tipo = ?, status = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (tag, tipo, status, atuador_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def excluir(atuador_id):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM atuadores WHERE id = ?", (atuador_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()


class LimitRepository:
    """Repositório dos limites relacionados ao disjuntor principal."""

    @staticmethod
    def listar_todos():
        conn = Database.get_connection()
        try:
            row_atuador = ActuatorRepository.obter_por_tag(TAG_DISJUNTOR_PRINCIPAL, conn)
            if row_atuador is None:
                return []
            rows = conn.execute(
                """
                SELECT limite_max_corrente, tensao_desarme
                FROM limites WHERE atuador_id = ? ORDER BY id ASC
                """,
                (row_atuador["id"],),
            ).fetchall()
            return [
                {
                    "Tensao": "" if row["tensao_desarme"] is None else str(row["tensao_desarme"]),
                    "Corrente": "" if row["limite_max_corrente"] is None else str(row["limite_max_corrente"]),
                }
                for row in rows
            ]
        finally:
            conn.close()

    @staticmethod
    def substituir_todos(limites):
        """Substitui as regras do disjuntor numa unica transação."""
        conn = Database.get_connection()
        try:
            with conn:
                atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL, conn)
                if atuador_id is None:
                    raise ValueError("Disjuntor principal não cadastrado no banco de dados.")

                conn.execute("DELETE FROM limites WHERE atuador_id = ?", (atuador_id,))
                for limite in limites:
                    tensao = float(limite["Tensao"])
                    corrente = float(limite["Corrente"])
                    if tensao <= 0 or corrente <= 0:
                        raise ValueError("Os limites devem ser maiores que zero.")
                    conn.execute(
                        """
                        INSERT INTO limites
                            (atuador_id, limite_max_corrente, tensao_desarme,
                             descricao, ultima_atualizacao)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (atuador_id, corrente, tensao, "Regra de segurança"),
                    )
        finally:
            conn.close()

    @staticmethod
    def criar(atuador_id, limite_max_corrente, tensao_desarme, descricao=""):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO limites
                        (atuador_id, limite_max_corrente, tensao_desarme, descricao)
                    VALUES (?, ?, ?, ?)
                    """,
                    (atuador_id, limite_max_corrente, tensao_desarme, descricao),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def atualizar(limite_id, limite_max_corrente, tensao_desarme, descricao=""):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE limites
                    SET limite_max_corrente = ?, tensao_desarme = ?,
                        descricao = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (limite_max_corrente, tensao_desarme, descricao, limite_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def excluir(limite_id):
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM limites WHERE id = ?", (limite_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()
