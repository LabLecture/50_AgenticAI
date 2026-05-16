"""
RAG 스크립트(rag01~rag07) 일괄 실행 검증.

각 스크립트를 subprocess 로 실행해 exit code 0 + 'Traceback' 미발견을 확인한다.
LLM/Cohere 키가 없는 경우에도 graceful skip 으로 정상 종료되어야 PASS.

사용 (BDAI/venv 활성화 후):
    python _verify_rag.py
"""
import subprocess
import sys
import os
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BDAI_ROOT = Path(__file__).parent

SCRIPTS = [
    "rag01_baseline.py",
    "rag02_hybrid_search.py",
    "rag03_reranking_local.py",
    "rag04_reranking_cohere.py",
    "rag05_query_transformation.py",
    "rag06_context_compression.py",
    "rag07_full_pipeline.py",
]


def run_one(name: str) -> tuple[bool, str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, name],
        cwd=str(BDAI_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=600,
    )
    output = (proc.stdout or "") + (proc.stderr or "")

    if "Traceback (most recent call last)" in output:
        tail = output.strip().splitlines()[-10:]
        return False, "Traceback 감지\n  | " + "\n  | ".join(tail)
    if proc.returncode != 0:
        return False, f"exit code {proc.returncode}"

    # graceful skip 인지, 실제 결과 출력인지 판단
    if "graceful" in output.lower() or "스킵합니다" in output or "스킵" in output:
        note = "(graceful skip 포함)"
    else:
        note = "(전체 실행)"
    return True, f"exit 0 {note}"


def main() -> int:
    print(f"Python: {sys.executable}\n")
    failures = 0
    for s in SCRIPTS:
        print(f"▶ {s} ...", flush=True)
        ok, msg = run_one(s)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}\n", flush=True)
        if not ok:
            failures += 1
    print("=" * 60)
    print(f"결과: {len(SCRIPTS) - failures}/{len(SCRIPTS)} 통과")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
