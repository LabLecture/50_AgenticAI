"""
01_extract.py — 사건 문서 8건에서 스키마 제약 구조화 추출 → extracted.json

supp_04/07(스키마 제약 추출)의 발전형. LLMGraphTransformer 대신 구조화 출력을
쓰는 이유: 이 도메인은 **이벤트의 date/amount 프로퍼티**가 핵심인데,
LLMGraphTransformer 는 노드/관계 타입 제약은 잘 해도 프로퍼티 추출이 약하다.
실무에서 "프로퍼티가 중요한 그래프"는 Pydantic 스키마 + 결정론적 적재가 정석.
"""
import json
from typing import List, Optional

from pydantic import BaseModel, Field

from _demo_common import (
    get_llm, structured, load_docs, banner, EXTRACT_JSON,
)


class Person(BaseModel):
    # Optional + 후처리 필터: free 모델이 '재무팀' 같은 무명 조직을
    # name=null 로 내보내는 경우가 있어 검증 실패 대신 걸러낸다.
    name: Optional[str] = Field(default=None, description="사람 이름 (예: 김재현)")
    company: Optional[str] = Field(default=None, description="소속 회사명 (예: 다온소프트)")
    title: Optional[str] = Field(default=None, description="직책 (예: 대표이사)")


class Event(BaseModel):
    type: str = Field(description="계약체결|지급|검수|내용증명|회신|하자보수 중 하나")
    date: str = Field(description="YYYY-MM-DD")
    amount: Optional[int] = Field(default=None, description="금전 이벤트면 원 단위 금액, 아니면 null")
    from_company: Optional[str] = Field(default=None, description="행위 주체 회사명")
    to_company: Optional[str] = Field(default=None, description="상대 회사명")
    summary: str = Field(description="이벤트 한 줄 요약 (한국어)")


class DocExtraction(BaseModel):
    doc_date: str = Field(description="문서 작성/발송일 YYYY-MM-DD")
    contract_id: Optional[str] = Field(default=None, description="언급된 계약번호")
    sender_person: Optional[str] = Field(default=None, description="발신인 이름 (공문/내용증명만)")
    receiver_person: Optional[str] = Field(default=None, description="수신인 이름 (공문/내용증명만)")
    signers: List[str] = Field(default_factory=list, description="계약서에 서명한 사람 이름들 (계약서만)")
    persons: List[Person] = Field(description="문서에 등장하는 모든 사람")
    events: List[Event] = Field(description="문서가 증거하는 사건들 (이 문서에서 직접 확인되는 것만)")


SYS = """너는 법률 문서에서 사실관계를 추출하는 분석가다. 반드시 아래 JSON 형식 그대로,
모든 키를 포함해 출력하라 (해당 없으면 null 또는 []):

{
  "doc_date": "YYYY-MM-DD (문서 작성/발송일)",
  "contract_id": "언급된 계약번호 또는 null",
  "sender_person": "발신인 이름 또는 null",
  "receiver_person": "수신인 이름 또는 null",
  "signers": ["계약서에 서명한 사람 이름들 (계약서가 아니면 [])"],
  "persons": [{"name": "이름", "company": "소속 회사명", "title": "직책"}],
  "events": [{"type": "계약체결|지급|검수|내용증명|회신|하자보수",
              "date": "YYYY-MM-DD", "amount": 36000000 또는 null,
              "from_company": "행위 주체 회사 또는 null",
              "to_company": "상대 회사 또는 null",
              "summary": "한 줄 요약"}]
}

규칙:
- 회사명은 '다온소프트', '한빛유통' 처럼 (주)/주식회사 없이 통일하라.
- events 는 이 문서가 직접 증거하는 사건만. 날짜가 명시된 것만 포함하라.
- 지급(입금) 이벤트는 type='지급', from_company=돈을 보낸 회사, to_company=받은 회사, amount=원 단위 정수.
- type='지급' 은 **실제 입금이 확인된 사실만**. 지급기일·청구·촉구·지급 예고·제안은 지급 이벤트가 아니다.
- 내용증명/회신 발송 자체도 하나의 이벤트다 (type='내용증명' 또는 '회신', 발송일 기준).
- 계약서 문서라면 계약 체결도 이벤트다 (type='계약체결', 체결일 기준).
- persons 에는 **이름이 명시된 개인만** 포함하라. '재무팀' 같은 무명 조직·부서는 제외."""


def main() -> None:
    banner("스키마 제약 구조화 추출 — 사건 문서 8건")
    llm = get_llm()
    if llm is None:
        print("❌ OPENROUTER_API_KEY 미설정"); return

    extractor = structured(llm, DocExtraction)
    results = {}
    for doc in load_docs():
        # free 모델은 간헐적으로 빈 응답을 내므로 최대 3회 재시도
        last_err = None
        for attempt in range(3):
            try:
                ext = extractor.invoke(
                    [("system", SYS),
                     ("user", f"[문서 ID: {doc['doc_id']} / {doc['title']}]\n\n{doc['text']}")])
                break
            except Exception as e:
                last_err = e
        else:
            print(f"  ❌ {doc['doc_id']} 추출 3회 실패: {last_err}")
            continue
        # 이름 없는 인물 제거 (무명 조직 방어)
        ext.persons = [p for p in ext.persons if p.name and p.company]
        results[doc["doc_id"]] = ext.model_dump()
        ev = ", ".join(f"{e['type']}({e['date']})" for e in results[doc["doc_id"]]["events"])
        print(f"  📄 {doc['doc_id']} {doc['title']}: 인물 {len(ext.persons)} / 이벤트 [{ev}]")

    EXTRACT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"\n  ✅ {EXTRACT_JSON.name} 저장 ({len(results)}건)")

    # ── 데모 핵심 사실 검증 ──────────────────────────────────────────
    all_events = [e for r in results.values() for e in r["events"]]
    # 같은 입금을 여러 문서가 언급할 수 있다 → (날짜, 금액) 으로 중복 제거
    pays = {(e["date"], e["amount"]) for e in all_events
            if e["type"] == "지급" and e["amount"]}
    total_paid = sum(a for _, a in pays)
    print(f"  검증: 지급 사실 {len(pays)}건(중복 제거), 총 {total_paid:,}원 "
          f"{'✅' if total_paid == 56_000_000 else '⚠ 기대값 56,000,000 과 다름'}")
    signers = results.get("doc01", {}).get("signers", [])
    print(f"  검증: 계약서 서명인 {signers} "
          f"{'✅' if set(signers) == {'김재현', '박성호'} else '⚠ 기대값과 다름'}")


if __name__ == "__main__":
    main()
