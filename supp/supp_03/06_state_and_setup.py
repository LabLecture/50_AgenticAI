"""
07_state_and_setup.py — State 정의 + LLM/임베딩 연결 확인

GraphState 는 4강 그래프 전체가 공유하는 타입 지정된 메모리.
모든 노드가 이 TypedDict 를 입력으로 받고, 변경 필드만 dict 로 반환한다.

이 파일은 단독 실행 시 "셋업이 잘 되어 있나?" 만 빠르게 검증한다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from typing import List, TypedDict

from _common import get_llm, get_embeddings, banner


class GraphState(TypedDict):
    """그래프 전체에서 공유되는 상태.

    question:    (재작성될 수 있는) 현재 질문
    documents:   현재까지 확보한 관련 문서 리스트
    generation:  LLM 이 생성한 답변
    retry_count: 반복 횟수 (무한 루프 방지용)
    web_search:  웹검색 폴백 필요 여부 플래그 ("Yes" / "No")
    """
    question: str
    documents: List[str]
    generation: str
    retry_count: int
    web_search: str


def main() -> None:
    banner("State 정의 + 셋업 점검")
    print(f"  GraphState 필드: {list(GraphState.__annotations__.keys())}")

    llm = get_llm()
    if llm is None:
        print("  ❌ OPENROUTER_API_KEY 미설정 — .env 확인 필요")
        return
    print(f"  ✅ LLM 준비:        {llm.model_name}  (base={llm.openai_api_base})")

    emb = get_embeddings()
    sample = emb.embed_query("LangGraph 는 무엇인가?")
    print(f"  ✅ 임베딩 준비:     dim={len(sample)}")

    print("\n  → 실행 전 모든 의존성이 살아 있음을 확인. 다음 단계: 07_indexing.py")


if __name__ == "__main__":
    main()
