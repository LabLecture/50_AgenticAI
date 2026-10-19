import os
import psycopg
from psycopg.rows import dict_row

class PostgreSqlDB:
    def __init__(self):
        # 연결 문자열이 없으면 빈 문자열 → psycopg 가 PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE 환경변수 사용
        self.db_config = os.getenv("POSTGRESQL_CONNECTION_STRING", "")
        
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