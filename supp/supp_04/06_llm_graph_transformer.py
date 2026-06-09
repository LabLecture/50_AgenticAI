"""
06_llm_graph_transformer.py — LLM 으로 비정형 텍스트에서 엔티티/관계 자동 추출

LLMGraphTransformer 는 LLM 호출로 (Person)-[FOUNDED]->(Company) 같은 트리플을 생성한다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from _common import get_llm, banner, llm_unavailable


SAMPLE_TEXT = """
Anthropic은 2021년 다리오 아모데이와 다니엘라 아모데이가 설립한 AI 안전 기업이다.
이 회사는 Claude라는 대규모 언어 모델을 개발했다.
Amazon은 Anthropic에 대규모 투자를 단행했으며, Anthropic의 모델은 AWS Bedrock 에서 제공된다.
다리오 아모데이는 이전에 OpenAI에서 연구를 이끌었다.
"""


def main() -> None:
    banner("LLMGraphTransformer — 텍스트 → 엔티티/관계 자동 추출")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    # ignore_tool_usage=True: free 모델은 function_calling 이 불안정해 prompt 기반 추출로 전환.
    # 내부적으로 JSON 출력 지시 프롬프트 + 파서를 사용하므로 schema 가 덜 엄격해도 OK.
    transformer = LLMGraphTransformer(llm=llm, ignore_tool_usage=True)
    docs = [Document(page_content=SAMPLE_TEXT.strip())]

    graph_docs = transformer.convert_to_graph_documents(docs)
    gd = graph_docs[0]

    print(f"\n📦 추출된 노드 ({len(gd.nodes)}개)")
    for n in gd.nodes:
        print(f"  - ({n.id}, type={n.type})")

    print(f"\n🔗 추출된 관계 ({len(gd.relationships)}개)")
    for r in gd.relationships:
        print(f"  - ({r.source.id})-[:{r.type}]->({r.target.id})")


if __name__ == "__main__":
    main()
