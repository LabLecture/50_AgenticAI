// 03_cypher_basics.cypher — Cypher 기초: CREATE / MATCH
//
// 실행 방법:
//   cypher-shell:  docker exec -i neo4j-graphrag cypher-shell -u neo4j -p test1234 < 03_cypher_basics.cypher
//   Neo4j Browser: http://localhost:7474 에서 각 문장을 하나씩 실행
//   Python wrapper: python _run_cypher.py 03_cypher_basics.cypher

// (0) 깨끗한 상태로 시작 (재실행 가능하게)
MATCH (n) DETACH DELETE n;

// (1) 노드 생성
CREATE (p:Person {name: '이건영', role: 'AI 강사'});
CREATE (c:Company {name: 'Anthropic', field: 'AI'});

// (2) 관계와 함께 생성
MATCH (p:Person {name: '이건영'}), (c:Company {name: 'Anthropic'})
CREATE (p)-[:WORKS_AT {since: 2024}]->(c);

// (3) 조회: 패턴 매칭
MATCH (p:Person {name: '이건영'})-[:WORKS_AT]->(c:Company)
RETURN p.name AS person, c.name AS company;

// (4) 전체 그래프 보기 (시각화에 유용)
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50;