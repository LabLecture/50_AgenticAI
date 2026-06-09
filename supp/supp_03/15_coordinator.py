"""
15_coordinator.py — Coordinator agent

가장 바깥의 *접수창구* 역할.
  - 인사/잡담 ("안녕", "고마워", "ㅎㅇ" 등) → coordinator 가 직접 응답하고 END
  - 정보 질의 ("에이전트 메모리란?", "비트코인 가격") → supervisor 에게 위임

분리 이유:
  - 사소한 인사를 supervisor 의 retrieve→grade→… 파이프라인에 태우면 LLM 호출 5+회 + 웹 검색
    까지 일어나는 *비용 폭발*. 일상 대화는 작은 분류기 한 번으로 막아낸다.
  - LangGraph multi-agent 의 "intent gate" 패턴 (수신 → 분기) 의 교과서 예시.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common import get_llm, binary_yesno

_llm = None


def _init():
    global _llm
    if _llm is None:
        _llm = get_llm()


# rule 기반 1 차 필터 — LLM 호출 자체를 줄임
_CHITCHAT_HINTS = (
    "안녕", "반가", "고마워", "감사", "잘 지내", "잘지내",
    "심심", "하이", "ㅎㅇ", "ㅎㅎ", "ㅋㅋ", "굿모닝", "굿이브닝",
)


def _rule_says_chitchat(text: str) -> bool:
    t = text.strip().lower()
    if len(t) <= 3:                       # 매우 짧으면 잡담일 가능성 높음
        return True
    return any(h in t for h in _CHITCHAT_HINTS)


def coordinator(state) -> dict:
    """의도 분류 → 잡담이면 직접 응답, 아니면 supervisor 로 위임."""
    _init()
    text = state["user_input"]
    print(f"  🎯 [coordinator] 입력: {text!r}")

    if _rule_says_chitchat(text):
        # rule 이 잡담이라 해도 LLM 으로 한 번 더 확인 (false positive 보호).
        # ⚠ 인사 + 정보질문 혼합 ("안녕, RAG가 뭐야?") 은 정보질의로 보내야 하므로
        #    예시를 명시해 판정 일관성 확보.
        yn = binary_yesno(
            _llm,
            "발화에 *지식/사실/방법 등 정보를 묻는 질문* 이 포함돼 있지 않으면 yes "
            "(= 순수 인사·안부·감사·잡담). 정보 질문이 하나라도 있으면 no.\n"
            "예시:\n"
            " - '안녕'                  → yes\n"
            " - '안녕! 오늘 기분 어때?' → yes  (안부 인사, 정보질문 없음)\n"
            " - '고마워'                → yes\n"
            " - '안녕, RAG 가 뭐야?'    → no  (RAG 정의 질문 포함)\n"
            " - '비트코인 가격 알려줘'  → no",
            f"발화: {text}",
        )
        if yn == "yes":
            print("     → 분류: chitchat (직접 응답)")
            reply = _llm.invoke(
                "다음 인사/잡담에 한국어로 한두 문장 친근히 답하세요. "
                "사실 정보·외부 지식 추가 금지.\n"
                f"발화: {text}\n응답:"
            ).content.strip()
            return {
                "route": "chitchat",
                "question": text,
                "answer": reply,
                "last_action": "coordinator",
            }

    print("     → 분류: info_query (supervisor 에 위임)")
    return {
        "route": "info_query",
        "question": text,
        "last_action": None,    # supervisor 가 첫 진입으로 인식하도록 명시적 None
    }


def coordinator_edge(state) -> str:
    """conditional edges 매핑용. chitchat → END, info_query → supervisor."""
    return "end" if state["route"] == "chitchat" else "supervisor"


if __name__ == "__main__":
    print("15_coordinator.py — coordinator 시그니처")
    print("  - coordinator       : (state) → {'route', 'question', ...}")
    print("  - coordinator_edge  : (state) → 'end' | 'supervisor'")
