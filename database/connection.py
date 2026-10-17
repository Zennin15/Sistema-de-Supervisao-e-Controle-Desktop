import sqlite3

class Database:
    DB_NAME = "smartgrid.db"

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """
        timeout configurado para mitigar o erro 'database is locked'.
        Faz o processo aguardar até 5 segundos caso outro processo esteja escrevendo.
        """
        conn = sqlite3.connect(cls.DB_NAME, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Garante a estrutura inicial no banco de dados."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            # Tabela do Atuador
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atuadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('LIGADO', 'DESLIGADO'))
                )
            """)
            # Tabela de Histórico/Auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atuador_id INTEGER NOT NULL,
                    status_registrado TEXT NOT NULL,
                    horario DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(atuador_id) REFERENCES atuadores(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS limites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    atuador_id INTEGER NOT NULL,
                    status_registrado TEXT NOT NULL,
                    horario DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(atuador_id) REFERENCES atuadores(id)
                )
            """)
            conn.commit()