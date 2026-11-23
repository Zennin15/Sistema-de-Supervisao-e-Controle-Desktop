import sqlite3
from datetime import datetime

from database.connection import Database


class HistoricoRepository:
    """
    Camada Model responsavel pela persistencia e consultas historicas de
    leituras de telemetria (tabela 'leituras') no SQLite.
    """
    def __init__(self, db_path: str | None = None):
        # Usa o mesmo caminho absoluto do restante da aplicacao por padrao,
        # evitando divergencia quando o processo roda fora da raiz do projeto.
        self.db_path = db_path or Database.DB_NAME

    def registrar_leitura(self, tensao: float, corrente: float, potencia: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO leituras (timestamp, tensao, corrente, potencia)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tensao, corrente, potencia),
            )

    def buscar_ultimas_leituras(self, limite_n: int = 100) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, tensao, corrente, potencia
                FROM leituras
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limite_n),)
            )
            linhas = [dict(row) for row in cursor.fetchall()]
            linhas.reverse()
            return linhas

    def buscar_por_intervalo(self, data_inicio: str, data_fim: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, tensao, corrente, potencia
                FROM leituras
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (data_inicio, data_fim)
            )
            return [dict(row) for row in cursor.fetchall()]
