#!/usr/bin/env bash
# 01_neo4j_docker.sh — Neo4j 5 + APOC 컨테이너 띄우기
#
# Windows PowerShell 사용자는 아래 명령을 한 줄로 실행:
#   docker run -d --name neo4j-graphrag -p 7474:7474 -p 7687:7687 `
#     -e NEO4J_AUTH=neo4j/test1234 -e NEO4J_PLUGINS='[\"apoc\"]' `
#     -e NEO4J_dbms_security_procedures_unrestricted=apoc.* neo4j:5
#
# 컨테이너 상태 확인:    docker ps --filter name=neo4j-graphrag
# Neo4j Browser:        http://localhost:7474  (login: neo4j / test1234)
# Bolt (앱 접속용):      bolt://localhost:7687
# 중지/제거:             docker rm -f neo4j-graphrag

docker run -d \
  --name neo4j-graphrag \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test1234 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_dbms_security_procedures_unrestricted='apoc.*' \
  neo4j:5

# 부팅 완료까지 ~30 초 — 다음 명령으로 ready 대기 가능:
#   until docker exec neo4j-graphrag cypher-shell -u neo4j -p test1234 "RETURN 1" >/dev/null 2>&1; do sleep 2; done
