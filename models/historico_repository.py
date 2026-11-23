import sqlite3

class HistoricoRepository:
    """
    Camada Model responsavel pelas consultas historicas no SQLite.
    """
    def __init__(self, db_path: str = "smartgrid.db"):
        self.db_path = db_path

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
