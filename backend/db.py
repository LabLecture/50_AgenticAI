import os
import psycopg
from psycopg.rows import dict_row
from psycopg.conninfo import make_conninfo

class PostgreSqlDB:
    def __init__(self):
        # [변경] POSTGRESQL_CONNECTION_STRING → embedding_postgre.py 와 같은 PG* 키 사용 (POSTGRES_* 는 예전 키 호환)
        self.db_config = make_conninfo(
            dbname   = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB", "postgres"),
            host     = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST", "localhost"),
            password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD"),
            port     = os.getenv("PGPORT") or os.getenv("DB_PORT", "5432"),
            user     = os.getenv("PGUSER") or os.getenv("POSTGRES_USER"),
        )
        
    def execute(self, query, params=None):
        """
        INSERT, UPDATE, DELETE 쿼리를 실행
        """
        try:
            with psycopg.connect(self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
        except Exception as e:
            print(f"Error executing query: {e}")

    def fetch_all(self, query, params=None):
        """
        SELECT 쿼리를 실행 후 모든 결과를 반환.
        """
        try:
            with psycopg.connect(self.db_config) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching all: {e}")
            return None

    def fetch_one(self, query, params=None):
        """
        SELECT 쿼리를 실행하고 첫 번째 결과만 반환.(값이 1개인경우 사용)
        """
        try:
            with psycopg.connect(self.db_config) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching one: {e}")
            return None