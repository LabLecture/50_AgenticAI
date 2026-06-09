"""
15_movie_text2cypher.py — Neo4j GenAI(neo4j-graphrag) Text2Cypher 영화 질의응답

흐름(블로그 2.6 응용과 동일):
  자연어 질문 → [Text2CypherRetriever] Cypher 자동 생성 → Neo4j 조회
              → [GraphRAG] 조회 결과를 자연어 답변으로

데이터셋 : 14_movies.cypher (Neo4j 'movies' — 영화 38편). 최초 실행 시 자동 적재(멱등).
실행      : cd supp/supp_04 ;  python ./15_movie_text2cypher.py
필요 패키지: neo4j-graphrag  (requirements.txt 에 포함)
키        : OPENROUTER_API_KEY (없으면 적재까지만 하고 LLM 질의는 스킵)
"""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # supp/.env (실행 위치와 무관)

import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG

HERE = Path(__file__).resolve().parent

# movies 데이터셋 스키마 (Text2Cypher 프롬프트에 주입 — 명시가 introspection 보다 안정적)
SCHEMA = """
Node properties:
Movie {title: STRING, released: INTEGER, tagline: STRING}
Person {name: STRING, born: INTEGER}
Relationships:
(:Person)-[:ACTED_IN {roles: LIST<STRING>}]->(:Movie)
(:Person)-[:DIRECTED]->(:Movie)
(:Person)-[:PRODUCED]->(:Movie)
(:Person)-[:WROTE]->(:Movie)
(:Person)-[:REVIEWED {rating: INTEGER}]->(:Movie)
""".strip()

# few-shot 예시 → Text2Cypher 품질↑ (소형 모델이 구버전 문법 쓰는 것 방지). cf. 2교시 §2.6 / 3교시 §3.x
EXAMPLES = [
    "USER INPUT: 'movies released in 1999' QUERY: MATCH (m:Movie) WHERE m.released = 1999 RETURN m.title",
    "USER INPUT: 'who acted in The Matrix' QUERY: MATCH (p:Person)-[:ACTED_IN]->(:Movie {title:'The Matrix'}) RETURN p.name",
]


def main():
    uri, user, pw = os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")
    if not (uri and user and pw):
        print("❌ NEO4J_* env 미설정 (supp/.env). 01_neo4j_docker.sh 로 컨테이너부터 띄우세요.")
        return
    driver = neo4j.GraphDatabase.driver(uri, auth=(user, pw))
    driver.verify_connectivity()

    # (1) movies 데이터셋 적재 — 비어 있을 때만 (MERGE 라 멱등)
    n = driver.execute_query("MATCH (m:Movie) RETURN count(m) AS c").records[0]["c"]
    if n == 0:
        print("⏳ movies 데이터셋 적재 중…")
        stmts = [s.strip() for s in (HERE / "14_movies.cypher").read_text(encoding="utf-8").split(";") if s.strip()]
        with driver.session() as s:
            for st in stmts:
                s.run(st)
        n = driver.execute_query("MATCH (m:Movie) RETURN count(m) AS c").records[0]["c"]
    print(f"🎬 Movie 노드: {n}")

    key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        print("⚠️ OPENROUTER_API_KEY 없음 — 적재까지만 하고 LLM 질의는 스킵합니다.")
        driver.close()
        return

    # (2) Neo4j GenAI: Text2CypherRetriever + GraphRAG
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
    llm = OpenAILLM(model_name=model, api_key=key,
                    base_url="https://openrouter.ai/api/v1", model_params={"temperature": 0})
    retriever = Text2CypherRetriever(driver=driver, llm=llm, neo4j_schema=SCHEMA, examples=EXAMPLES)
    rag = GraphRAG(retriever=retriever, llm=llm)
    print(f"🤖 LLM: {model}\n")

    for q in ["Who directed The Matrix?",
              "List the movies Tom Hanks acted in.",
              "Which movies were released in 1999?"]:
        print("=" * 64 + f"\n🙋 {q}")
        try:
            r = retriever.search(query_text=q)
            print("  ⚙  자동생성 Cypher:", (r.metadata or {}).get("cypher"))
            print("  💬 답변:", rag.search(query_text=q).answer, "\n")
        except Exception as e:
            print("  ❌", type(e).__name__, str(e)[:180], "\n")
    driver.close()


if __name__ == "__main__":
    main()
