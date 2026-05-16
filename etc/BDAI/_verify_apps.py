"""
각 Streamlit 앱을 헤드리스 모드로 띄워 시작 시점 에러를 확인하는 검증 스크립트.

성공 조건: "You can now view your Streamlit app" 메시지가 출력되고,
        "Error" / "Traceback" 패턴이 stderr에 나타나지 않음.

사용 (BDAI/venv 활성화 후):
    python _verify_apps.py
"""
import subprocess
import sys
import time
import threading
import os
import urllib.request
from pathlib import Path

# Windows 콘솔 cp949 -> UTF-8 강제
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BDAI_ROOT = Path(__file__).parent

APPS = [
    # (description, working_dir, target_file, port)
    ("st01_basics",       BDAI_ROOT, "st01_basics.py",       8601),
    ("st02_chatbot",      BDAI_ROOT, "st02_chatbot.py",      8602),
    ("st03_sidebar",      BDAI_ROOT, "st03_sidebar.py",      8603),
    ("st04_file_upload",  BDAI_ROOT, "st04_file_upload.py",  8604),
    ("st05_multipage",    BDAI_ROOT / "st05_multipage", "app.py", 8605),
]


def run_one(name: str, cwd: Path, target: str, port: int) -> tuple[bool, str]:
    """Streamlit 앱을 headless 로 띄워 startup이 정상인지 확인."""
    cmd = [
        sys.executable, "-m", "streamlit", "run", target,
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.runOnSave", "false",
        "--global.developmentMode", "false",
    ]
    log_lines: list[str] = []
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    # 백그라운드 reader
    def _reader() -> None:
        if proc.stdout is None:
            return
        for line in proc.stdout:
            log_lines.append(line.rstrip("\n"))

    t = threading.Thread(target=_reader, daemon=True)
    t.start()

    # 최대 25초 대기. "You can now view" 발견 시 즉시 다음 단계로.
    deadline = time.monotonic() + 25
    started = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break  # 프로세스가 죽었음
        if any("You can now view" in ln or "Local URL:" in ln for ln in log_lines):
            started = True
            break
        time.sleep(0.3)

    # 시작했으면 HTTP 요청으로 페이지 렌더 시도 (런타임 에러 트리거)
    http_ok = False
    http_err = ""
    if started:
        try:
            time.sleep(1.0)  # 서버 안정화
            with urllib.request.urlopen(f"http://localhost:{port}/", timeout=10) as resp:
                http_ok = (resp.status == 200)
            time.sleep(2.0)  # 스크립트 실행 시간 확보 (에러 로그가 나타나도록)
        except Exception as e:
            http_err = f"HTTP 요청 실패: {e}"

    # 종료
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)

    log_text = "\n".join(log_lines)

    # 에러 패턴 체크 (시작 단계와 첫 페이지 렌더에서 발생한 에러)
    error_markers = ["Traceback (most recent call last)", "ModuleNotFoundError", "SyntaxError"]
    found_errors = [m for m in error_markers if m in log_text]

    if not started:
        return False, f"시작 실패 (25초 안에 'You can now view' 미발견)\n--- LOG ---\n{log_text[-2000:]}"
    if found_errors:
        return False, f"런타임 에러 감지: {found_errors}\n--- LOG ---\n{log_text[-2000:]}"
    if http_err:
        return False, f"{http_err}\n--- LOG ---\n{log_text[-2000:]}"
    if not http_ok:
        return False, f"HTTP 200 응답 안 옴\n--- LOG ---\n{log_text[-2000:]}"

    return True, f"✅ startup OK · HTTP 200 · 에러 없음 (log {len(log_lines)} lines)"


def main() -> int:
    print(f"Python: {sys.executable}\n")
    failures = 0
    for name, cwd, target, port in APPS:
        print(f"▶ {name} (port {port}) ...", flush=True)
        ok, msg = run_one(name, cwd, target, port)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}\n", flush=True)
        if not ok:
            failures += 1
    print("=" * 60)
    print(f"결과: {len(APPS) - failures}/{len(APPS)} 통과")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
