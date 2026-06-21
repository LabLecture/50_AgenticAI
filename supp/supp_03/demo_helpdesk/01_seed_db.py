"""
01_seed_db.py — PostgreSQL 테이블 생성 + 시드 데이터 적재.

테이블 3개:
  employees(emp_id, name, dept, position, hire_date)
  leaves(emp_id, year, total_days, carried_days, used_days)   # 연차 현황
  expenses(emp_id, use_date, category, amount, status)        # 경비 정산

데모 주인공: E1003 김민준 — 2026년 기본 15일 + 이월 3일 - 사용 6일 = 잔여 12일.
"""
from _demo_common import get_conn, banner

DDL = """
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS leaves;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    emp_id    VARCHAR(8) PRIMARY KEY,
    name      VARCHAR(20) NOT NULL,
    dept      VARCHAR(30) NOT NULL,
    position  VARCHAR(20) NOT NULL,
    hire_date DATE NOT NULL
);

CREATE TABLE leaves (
    emp_id       VARCHAR(8) REFERENCES employees(emp_id),
    year         INT NOT NULL,
    total_days   NUMERIC(4,1) NOT NULL,   -- 당해 발생 연차
    carried_days NUMERIC(4,1) NOT NULL,   -- 전년도 이월분 (6/30 한도)
    used_days    NUMERIC(4,1) NOT NULL,
    PRIMARY KEY (emp_id, year)
);

CREATE TABLE expenses (
    id       SERIAL PRIMARY KEY,
    emp_id   VARCHAR(8) REFERENCES employees(emp_id),
    use_date DATE NOT NULL,
    category VARCHAR(20) NOT NULL,        -- 식대/야근식대/출장/회식/접대
    amount   INT NOT NULL,
    status   VARCHAR(10) NOT NULL         -- 승인/반려/검토중
);
"""

EMPLOYEES = [
    ("E1001", "박서연", "인사팀",   "팀장", "2018-03-02"),
    ("E1002", "이도현", "개발팀",   "책임", "2020-07-13"),
    ("E1003", "김민준", "개발팀",   "선임", "2022-01-10"),
    ("E1004", "최지우", "영업팀",   "대리", "2023-05-22"),
    ("E1005", "정하은", "재무팀",   "사원", "2025-02-03"),
]

LEAVES = [
    # 2025년 (작년)
    ("E1001", 2025, 19, 2, 17),
    ("E1002", 2025, 16, 0, 14),
    ("E1003", 2025, 15, 0, 12),   # 미사용 3일 → 2026 으로 이월
    ("E1004", 2025, 15, 0, 15),
    ("E1005", 2025, 11, 0,  9),
    # 2026년 (올해)
    ("E1001", 2026, 19, 2,  8),
    ("E1002", 2026, 17, 2,  5),
    ("E1003", 2026, 15, 3,  6),   # 15 + 이월3 - 6 = 잔여 12일  ← 데모 핵심
    ("E1004", 2026, 15, 0,  4),
    ("E1005", 2026, 15, 2,  3),
]

EXPENSES = [
    ("E1003", "2026-05-12", "야근식대",  14000, "승인"),
    ("E1003", "2026-05-28", "식대",      12000, "승인"),
    ("E1003", "2026-06-02", "회식",      48000, "검토중"),
    ("E1004", "2026-05-30", "출장",     120000, "승인"),
    ("E1004", "2026-06-05", "접대",     350000, "반려"),   # 30만 초과 사전품의 누락
    ("E1002", "2026-06-08", "식대",      15000, "반려"),   # 한도 초과
]


def main() -> None:
    banner("PostgreSQL 시드 — employees / leaves / expenses")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(DDL)
        cur.executemany(
            "INSERT INTO employees VALUES (%s,%s,%s,%s,%s)", EMPLOYEES)
        cur.executemany(
            "INSERT INTO leaves VALUES (%s,%s,%s,%s,%s)", LEAVES)
        cur.executemany(
            "INSERT INTO expenses (emp_id,use_date,category,amount,status) "
            "VALUES (%s,%s,%s,%s,%s)", EXPENSES)

        cur.execute("SELECT count(*) FROM employees"); n_e = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM leaves");    n_l = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM expenses");  n_x = cur.fetchone()[0]
    print(f"  ✅ employees {n_e} / leaves {n_l} / expenses {n_x} rows")

    # 데모 핵심 수치 검증: E1003 잔여 연차 = 12
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT total_days + carried_days - used_days
            FROM leaves WHERE emp_id='E1003' AND year=2026""")
        remain = cur.fetchone()[0]
    assert float(remain) == 12.0, f"E1003 잔여 연차가 12가 아님: {remain}"
    print(f"  ✅ 데모 검증: E1003(김민준) 2026 잔여 연차 = {remain}일")


if __name__ == "__main__":
    main()
