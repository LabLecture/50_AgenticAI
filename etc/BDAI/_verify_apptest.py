"""
Streamlit AppTest 프레임워크를 사용한 in-process 검증.
HTTP 서버 띄우기 없이 스크립트를 직접 실행해 예외/에러를 잡는다.

사용 (BDAI/venv 활성화 후):
    python _verify_apptest.py
"""
import sys
import os
from pathlib import Path

# UTF-8 강제 (Windows cp949 회피)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from streamlit.testing.v1 import AppTest

BDAI_ROOT = Path(__file__).parent
MULTIPAGE_DIR = BDAI_ROOT / "st05_multipage"

# (description, file_path, must_chdir_to)
TARGETS = [
    ("st01_basics",       BDAI_ROOT / "st01_basics.py",                                  None),
    ("st02_chatbot",      BDAI_ROOT / "st02_chatbot.py",                                 None),
    ("st03_sidebar",      BDAI_ROOT / "st03_sidebar.py",                                 None),
    ("st04_file_upload",  BDAI_ROOT / "st04_file_upload.py",                             None),
    # 멀티페이지: app.py 진입점
    ("st05_app",          MULTIPAGE_DIR / "app.py",                                      MULTIPAGE_DIR),
    ("st05_chat_page",    MULTIPAGE_DIR / "pages" / "1_💬_Chat.py",                      MULTIPAGE_DIR),
    ("st05_docs_page",    MULTIPAGE_DIR / "pages" / "2_📄_Documents.py",                 MULTIPAGE_DIR),
    ("st05_dash_page",    MULTIPAGE_DIR / "pages" / "3_📊_Dashboard.py",                 MULTIPAGE_DIR),
]


def run_one(name: str, file_path: Path, chdir_to: Path | None) -> tuple[bool, str]:
    saved_cwd = os.getcwd()
    saved_path = list(sys.path)
    try:
        if chdir_to is not None:
            os.chdir(str(chdir_to))
            sys.path.insert(0, str(chdir_to))
        at = AppTest.from_file(str(file_path), default_timeout=15)
        at.run()
        if at.exception:
            errs = [str(e.value) if hasattr(e, "value") else str(e) for e in at.exception]
            return False, f"실행 중 예외 발생: {errs}"
        return True, "✅ 스크립트 실행 OK · 예외 없음"
    except Exception as e:
        return False, f"AppTest 자체 실패: {type(e).__name__}: {e}"
    finally:
        os.chdir(saved_cwd)
        sys.path[:] = saved_path


def main() -> int:
    print(f"Python: {sys.executable}")
    import streamlit as st
    print(f"Streamlit: {st.__version__}\n")

    failures = 0
    for name, path, chdir_to in TARGETS:
        print(f"▶ {name} ...", flush=True)
        ok, msg = run_one(name, path, chdir_to)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}\n", flush=True)
        if not ok:
            failures += 1
    print("=" * 60)
    print(f"결과: {len(TARGETS) - failures}/{len(TARGETS)} 통과")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
