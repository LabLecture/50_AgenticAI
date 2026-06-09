// 04_merge_and_multihop.cypher — MERGE 와 멀티홉 / 집계
//
// MERGE 는 "있으면 매칭, 없으면 생성" 멱등 연산. 실무에서 CREATE 대신 거의 항상 사용.
// 가변 길이 경로 `*1..3` 은 벡터 RAG 가 풀 수 없는 multi-hop 질의의 핵심 도구.
//
// 그래프: 4 Company + 5 관계
//   Anthropic -[:PARTNERED_WITH]-> Amazon
//   Amazon    -[:OWNS]->           AWS
//   AWS       -[:HOSTS]->          Bedrock Customer
//   Anthropic -[:USES]->           AWS                (인프라 직접 사용)
//   Anthropic -[:SERVES]->         Bedrock Customer   (서비스 직접 제공)
// (브라우저 색은 '관계 타입'별로 자동 지정 — USES/SERVES 칩 클릭해 색 변경 가능)

// (0) 초기화
MATCH (n) DETACH DELETE n;

// (1) 노드 — MERGE: 중복 없는 멱등 적재
MERGE (a:Company {name: 'Anthropic'});
MERGE (b:Company {name: 'Amazon'});
MERGE (c:Company {name: 'AWS'});
MERGE (d:Company {name: 'Bedrock Customer'});

// (2) 관계 5개
MATCH (a:Company {name: 'Anthropic'}), (b:Company {name: 'Amazon'})
MERGE (a)-[:PARTNERED_WITH]->(b);
MATCH (b:Company {name: 'Amazon'}), (c:Company {name: 'AWS'})
MERGE (b)-[:OWNS]->(c);
MATCH (c:Company {name: 'AWS'}), (d:Company {name: 'Bedrock Customer'})
MERGE (c)-[:HOSTS]->(d);
MATCH (a:Company {name: 'Anthropic'}), (c:Company {name: 'AWS'})
MERGE (a)-[:USES]->(c);
MATCH (a:Company {name: 'Anthropic'}), (d:Company {name: 'Bedrock Customer'})
MERGE (a)-[:SERVES]->(d);

// (3) 표시용 속성: degree(연결 수) + label("이름 (연결수)")
//     브라우저에서 Caption 을 label 로 바꾸면 노드에 "Amazon (2)" 처럼 이름+숫자 표시
MATCH (x:Company)
OPTIONAL MATCH (x)-[rel]-()
WITH x, count(rel) AS deg
SET x.degree = deg,
    x.label  = x.name + ' (' + toString(deg) + ')';

// (4) 멀티홉: Anthropic 에서 1~3홉으로 닿는 회사
MATCH (start:Company {name: 'Anthropic'})-[*1..3]->(other:Company)
RETURN DISTINCT other.name AS reachable_company;

// (5) 집계: 가장 연결이 많은 회사 (벡터 RAG 로는 불가능한 질의)
//     → Anthropic 3, AWS 3, Amazon 2, Bedrock Customer 2
MATCH (x:Company)-[r]-()
RETURN x.name AS company, count(r) AS connections
ORDER BY connections DESC;

// (6) 브라우저 관계도(화살표)로 보기 — 노드+관계를 RETURN해야 Graph 탭이 보임
//     MATCH (x:Company)-[r]-(m) RETURN x, r, m;
