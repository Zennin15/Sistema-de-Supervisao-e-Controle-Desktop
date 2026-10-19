from pathlib import Path
import sqlite3


class Database:
    """Gerencia conexões e inicialização do banco SQLite do Smart Grid."""

    DB_NAME = str(Path(__file__).resolve().parents[1] / "smartgrid.db")

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Abre uma conexao com timeout e chaves estrangeiras habilitadas."""
        if cls.DB_NAME != ":memory:":
            Path(cls.DB_NAME).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(cls.DB_NAME, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def _sql_atuadores(nome_tabela="atuadores") -> str:
        if nome_tabela == "atuadores_novo":
            return """
                CREATE TABLE atuadores_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('ABERTO', 'FECHADO')),
                    ultima_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
        return """
            CREATE TABLE IF NOT EXISTS atuadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('ABERTO', 'FECHADO')),
                ultima_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """

    @staticmethod
    def _sql_historico(nome_tabela="historico_eventos") -> str:
        if nome_tabela == "historico_eventos_novo":
            return """
                CREATE TABLE historico_eventos_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atuador_id INTEGER,
                    data_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tipo_evento TEXT NOT NULL,
                    valor_medido REAL,
                    descricao TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(atuador_id) REFERENCES atuadores(id) ON DELETE SET NULL
                )
            """
        return """
            CREATE TABLE IF NOT EXISTS historico_eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atuador_id INTEGER,
                data_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                tipo_evento TEXT NOT NULL,
                valor_medido REAL,
                descricao TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(atuador_id) REFERENCES atuadores(id) ON DELETE SET NULL
            )
        """

    @staticmethod
    def _sql_limites(nome_tabela="limites") -> str:
        if nome_tabela == "limites_novo":
            return """
                CREATE TABLE limites_novo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atuador_id INTEGER NOT NULL,
                    limite_max_corrente REAL CHECK(limite_max_corrente IS NULL OR limite_max_corrente > 0),
                    tensao_desarme REAL CHECK(tensao_desarme IS NULL OR tensao_desarme > 0),
                    descricao TEXT NOT NULL DEFAULT '',
                    ultima_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(atuador_id) REFERENCES atuadores(id) ON DELETE CASCADE
                )
            """
        return """
            CREATE TABLE IF NOT EXISTS limites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atuador_id INTEGER NOT NULL,
                limite_max_corrente REAL CHECK(limite_max_corrente IS NULL OR limite_max_corrente > 0),
                tensao_desarme REAL CHECK(tensao_desarme IS NULL OR tensao_desarme > 0),
                descricao TEXT NOT NULL DEFAULT '',
                ultima_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(atuador_id) REFERENCES atuadores(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def _migrar_esquema_antigo(cls) -> None:
        """Recria tabelas antigas para aplicar as restrições sem perder dados."""
        if cls.DB_NAME == ":memory:" or not Path(cls.DB_NAME).exists():
            return

        conn = sqlite3.connect(cls.DB_NAME, timeout=5.0)
        try:
            tabelas = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            tabelas_projeto = {"atuadores", "historico_eventos", "limites"}
            if not (tabelas & tabelas_projeto):
                return

            sql_atuadores = ""
            sql_historico = ""
            sql_limites = ""
            if "atuadores" in tabelas:
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                    ("atuadores",),
                ).fetchone()
                sql_atuadores = "".join((row[0] or "").upper().split()) if row else ""
            if "historico_eventos" in tabelas:
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                    ("historico_eventos",),
                ).fetchone()
                sql_historico = "".join((row[0] or "").upper().split()) if row else ""
            if "limites" in tabelas:
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                    ("limites",),
                ).fetchone()
                sql_limites = "".join((row[0] or "").upper().split()) if row else ""

            esquema_atuadores_ok = (
                "CHECK(STATUSIN('ABERTO','FECHADO'))" in sql_atuadores
                and "TAGTEXTNOTNULL" in sql_atuadores
                and "TIPOTEXTNOTNULL" in sql_atuadores
                and "ULTIMA_ATUALIZACAOTEXTNOTNULL" in sql_atuadores
            )
            esquema_historico_ok = (
                "DATA_HORATEXTNOTNULL" in sql_historico
                and "TIPO_EVENTOTEXTNOTNULL" in sql_historico
                and "DESCRICAOTEXTNOTNULL" in sql_historico
            )
            esquema_limites_ok = (
                "ATUADOR_IDINTEGERNOTNULL" in sql_limites
                and "DESCRICAOTEXTNOTNULL" in sql_limites
                and "ULTIMA_ATUALIZACAOTEXTNOTNULL" in sql_limites
            )
            if esquema_atuadores_ok and esquema_historico_ok and esquema_limites_ok:
                return

            # A migração e feita com foreign_keys desligado somente nesta conexao,
            # pois as tabelas antigas precisam ser substituidas em conjunto.
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("BEGIN;")
            conn.execute("DROP TABLE IF EXISTS atuadores_novo;")
            conn.execute("DROP TABLE IF EXISTS historico_eventos_novo;")
            conn.execute("DROP TABLE IF EXISTS limites_novo;")
            conn.execute(cls._sql_atuadores("atuadores_novo"))
            conn.execute(cls._sql_historico("historico_eventos_novo"))
            conn.execute(cls._sql_limites("limites_novo"))

            if "atuadores" in tabelas:
                conn.execute(
                    """
                    INSERT INTO atuadores_novo
                        (id, tag, tipo, status, ultima_atualizacao)
                    SELECT id, tag, tipo,
                           CASE UPPER(status)
                               WHEN 'LIGADO' THEN 'FECHADO'
                               WHEN 'DESLIGADO' THEN 'ABERTO'
                               WHEN 'FECHADO' THEN 'FECHADO'
                               WHEN 'ABERTO' THEN 'ABERTO'
                               ELSE 'FECHADO'
                           END,
                           COALESCE(ultima_atualizacao, CURRENT_TIMESTAMP)
                    FROM atuadores
                    """
                )

            if "historico_eventos" in tabelas:
                conn.execute(
                    """
                    INSERT INTO historico_eventos_novo
                        (id, atuador_id, data_hora, tipo_evento, valor_medido, descricao)
                    SELECT id,
                           CASE WHEN atuador_id IN (SELECT id FROM atuadores_novo)
                                THEN atuador_id ELSE NULL END,
                           COALESCE(data_hora, CURRENT_TIMESTAMP),
                           COALESCE(NULLIF(tipo_evento, ''), 'Evento'),
                           valor_medido,
                           COALESCE(descricao, '')
                    FROM historico_eventos
                    """
                )

            if "limites" in tabelas:
                conn.execute(
                    """
                    INSERT INTO limites_novo
                        (id, atuador_id, limite_max_corrente, tensao_desarme,
                         descricao, ultima_atualizacao)
                    SELECT id, atuador_id, limite_max_corrente, tensao_desarme,
                           COALESCE(descricao, ''),
                           COALESCE(ultima_atualizacao, CURRENT_TIMESTAMP)
                    FROM limites
                    WHERE atuador_id IN (SELECT id FROM atuadores_novo)
                    """
                )

            # Apaga primeiro as tabelas dependentes. Os IDs sao preservados na copia.
            conn.execute("DROP TABLE IF EXISTS historico_eventos;")
            conn.execute("DROP TABLE IF EXISTS limites;")
            conn.execute("DROP TABLE IF EXISTS atuadores;")
            conn.execute("ALTER TABLE atuadores_novo RENAME TO atuadores;")
            conn.execute("ALTER TABLE historico_eventos_novo RENAME TO historico_eventos;")
            conn.execute("ALTER TABLE limites_novo RENAME TO limites;")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
            finally:
                conn.close()

    @classmethod
    def init_db(cls) -> None:
        """Cria ou atualiza o esquema relacional e os atuadores padrão."""
        cls._migrar_esquema_antigo()
        conn = cls.get_connection()
        try:
            with conn:
                conn.execute(cls._sql_atuadores())
                conn.execute(cls._sql_historico())
                conn.execute(cls._sql_limites())

                conn.execute(
                    """
                    INSERT OR IGNORE INTO atuadores
                        (tag, tipo, status, ultima_atualizacao)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    ("DISJUNTOR_PRINCIPAL", "DISJUNTOR", "FECHADO"),
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO atuadores
                        (tag, tipo, status, ultima_atualizacao)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    ("RELE_EMERGENCIA", "RELE", "FECHADO"),
                )
        finally:
            conn.close()
