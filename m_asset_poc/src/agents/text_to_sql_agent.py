"""
Text-to-SQL agent implementation using LangGraph.
Converts natural language queries to SQL queries with vector search assistance.
"""

import re
import traceback
from typing import Annotated, List, Sequence, Optional, Literal
from typing_extensions import TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from ..core.config import config
from ..core.database import db_manager
from ..core.vector_store import vector_store_manager
from ..core.langfuse_manager import langfuse_manager
from ..core.llm_cache_manager import llm_cache_manager
from ..utils.default_schema import get_default_schema, get_basic_schema_examples

# Langfuse imports
try:
    from langfuse.langchain import CallbackHandler
    from langfuse import observe, get_client
    LANGFUSE_AVAILABLE = True
except ImportError:
    CallbackHandler = None
    LANGFUSE_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)


class TextToSqlState(TypedDict):
    """Text-to-SQL 상태 정의"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    retrieved_schema_examples: List[str]
    retrieved_sample_query: List[str]
    relevant_tables: List[str]
    table_schema: str
    final_query: str
    error_message: Optional[str]
    query_result: str
    retry_count: int
    final_answer: Optional[str]


class TextToSqlAgent:
    """Text-to-SQL 에이전트 클래스"""
    
    def __init__(self):
        """Text-to-SQL 에이전트 초기화"""
        self._llm = None
        self._sql_tools = None
        self._graph = None
        self._initialize_components()
        
    def _initialize_components(self):
        """에이전트 구성 요소 초기화"""
        # LLM 초기화
        self._llm = OpenAI(
            model=config.vllm.model_name,
            openai_api_key=config.vllm.api_key,
            openai_api_base=config.vllm.server_url,
            temperature=config.vllm.temperature
        )
        
        # 데이터베이스 초기화
        db_manager.initialize_sync_db()
        
        # SQL 툴킷 초기화
        toolkit = db_manager.get_sql_toolkit(self._llm)
        tools = toolkit.get_tools()
        
        # 개별 도구 추출
        self._sql_tools = {
            'list_tables': next(tool for tool in tools if tool.name == "sql_db_list_tables"),
            'get_schema': next(tool for tool in tools if tool.name == "sql_db_schema"),
            'query_sql': next(tool for tool in tools if tool.name == "sql_db_query"),
            'query_checker': next(tool for tool in tools if tool.name == "sql_db_query_checker")
        }
        
        # 벡터 스토어 초기화
        vector_store_manager.initialize()
        
        # LLM 캐시 매니저 초기화
        llm_cache_manager.initialize()
        
        # 그래프 구성
        self._build_graph()
        
        logger.info("Text-to-SQL agent initialized successfully")
    
    def _get_initial_user_query(self, state: TextToSqlState) -> str:
        """상태에서 초기 사용자 쿼리 추출"""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""
    
    def _get_schema_from_vector_db(self, state: TextToSqlState) -> dict:
        """벡터 DB에서 스키마 예제 검색 (실패 시 기본 스키마 사용)"""
        user_query = self._get_initial_user_query(state)
        if not user_query:
            return {"retrieved_schema_examples": [], "error_message": None}
        
        try:
            # 스키마 예제 검색
            retrieved_examples = vector_store_manager.search_schema_examples(user_query, limit=3)
            
            # 검색 결과가 없으면 기본 스키마 사용
            if not retrieved_examples:
                logger.warning("No schema examples found in vector DB, using default schema")
                retrieved_examples = get_basic_schema_examples()
                message_content = "Vector DB returned no results. Using default schema information:\n\n"
                message_content += get_default_schema()
            else:
                # 검색 결과 메시지 생성
                message_content = vector_store_manager.get_schema_search_results_message(user_query, limit=3)
            
            return {
                **state,
                "messages": [AIMessage(content=message_content)],
                "retrieved_schema_examples": retrieved_examples,
                "error_message": None
            }
            
        except Exception as e:
            logger.error(f"Error during schema vector DB query: {e}")
            logger.info("Falling back to default schema")
            
            # 벡터 DB 오류 시 기본 스키마 사용
            default_examples = get_basic_schema_examples()
            message_content = f"Warning: Vector DB query failed ({e}). Using default schema:\n\n"
            message_content += get_default_schema()
            
            return {
                **state,
                "messages": [AIMessage(content=message_content)],
                "retrieved_schema_examples": default_examples,
                "error_message": None
            }
    
    def _get_sample_query_from_vector_db(self, state: TextToSqlState) -> dict:
        """벡터 DB에서 샘플 쿼리 검색"""
        user_query = self._get_initial_user_query(state)
        if not user_query:
            return {"retrieved_sample_query": [], "error_message": None}
        
        logger.info(f"Querying Vector DB(sample_query) for: '{user_query}'")
        
        try:
            # 샘플 쿼리 검색
            retrieved_samples = vector_store_manager.search_sample_queries(user_query, limit=2)
            
            # 검색 결과 메시지 생성
            message_content = vector_store_manager.get_sample_search_results_message(user_query, limit=2)
            
            logger.info(f"Found {len(retrieved_samples)} SQL examples in Vector DB")
            
            return {
                **state,
                "messages": [AIMessage(content=message_content)],
                "retrieved_sample_query": retrieved_samples,
                "error_message": None
            }
            
        except Exception as e:
            logger.error(f"Error during sample query vector DB search: {e}")
            return {
                **state,  # 상태 보존 (retry_count 유지)
                "messages": [AIMessage(content=f"Warning: Vector DB query failed. {e}")],
                "retrieved_sample_query": [],
                "error_message": None
            }
    
    def _generate_sql_query_with_schema(self, state: TextToSqlState) -> dict:
        """스키마 정보를 사용하여 SQL 쿼리 생성"""
        user_query = self._get_initial_user_query(state)
        retrieved_schema_examples = state.get("retrieved_schema_examples", [])
        previous_error = state.get("error_message")
        
        logger.info(f"Generating SQL for query with_schema: '{user_query}'")
        if previous_error:
            logger.info(f"Attempting to correct previous error: {previous_error}")
        
        if not retrieved_schema_examples:
            # 스키마가 없는 경우 기본 스키마 사용
            logger.warning("No schema examples available, using default schema")
            retrieved_schema_examples = get_basic_schema_examples()
            
            if not retrieved_schema_examples:
                return {
                    "messages": [AIMessage(content="Cannot generate SQL: No table schema available.")],
                    "final_query": "",
                    "error_message": "Missing table schema"
                }
        
        # SQL 생성 프롬프트 구성
        system_prompt = self._build_sql_generation_prompt()
        
        evidences = "회사명or종목명-exchange_kosdaq_stock_master.kor_name_small"
        evidences += "배당수익률-exchange_kosdaq_stock_master.dividend_yield"
        
        # 이전 에러가 있으면 프롬프트에 포함
        if previous_error:
            error_context = f"\n\nPrevious SQL execution failed with error:\n{previous_error}\n\nPlease analyze the error and correct the SQL query accordingly."
            prompt = system_prompt.format(
                db_details=retrieved_schema_examples,
                evidence=evidences,
                question=user_query + error_context
            )
        else:
            prompt = system_prompt.format(
                db_details=retrieved_schema_examples,
                evidence=evidences,
                question=user_query
            )
        
        # 캐시에서 SQL 조회 시도
        schema_info = str(retrieved_schema_examples)
        cached_sql = llm_cache_manager.get_cached_sql(user_query, schema_info)
        
        if cached_sql:
            logger.info(f"Using cached SQL query: {cached_sql}")
            retry_count = state.get("retry_count", 0)
            return {
                **state,
                "messages": [AIMessage(content=f"Generated SQL query (from cache):\n```sql\n{cached_sql}\n```")],
                "final_query": cached_sql,
                "error_message": None,
                "retry_count": retry_count + 1
            }
        
        try:
            retry_count = state.get("retry_count", 0)
            response = self._llm.invoke(prompt)
            logger.info(f"LLM response: {response}")
            
            # SQL 쿼리 추출
            sql_query = self._extract_sql_from_response(response)
            logger.info(f"Generated SQL (Attempt): {sql_query}")
            
            # 성공적으로 생성된 SQL 캐싱
            if sql_query:
                llm_cache_manager.set_cached_sql(user_query, schema_info, sql_query)
            
            return {
                **state,
                "messages": [AIMessage(content=f"Generated SQL query attempt:\n```sql\n{sql_query}\n```")],
                "final_query": sql_query,
                "error_message": None,
                "retry_count": retry_count + 1
            }
            
        except Exception as e:
            logger.error(f"Error invoking LLM for SQL generation: {e}")
            err_msg = f"LLM failed during query generation: {e}"
            return {
                **state,
                "messages": [AIMessage(content=f"Error generating SQL: {err_msg}")],
                "final_query": "",
                "error_message": err_msg,
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    def _generate_sql_query_with_sample(self, state: TextToSqlState) -> dict:
        """샘플 쿼리를 사용하여 SQL 쿼리 생성"""
        user_query = self._get_initial_user_query(state)
        retrieved_schema_examples = state.get("retrieved_schema_examples", [])
        retrieved_sample_query = state.get("retrieved_sample_query", [])
        previous_error = state.get("error_message")
        
        logger.info(f"Generating SQL for query with_sample: '{user_query}'")
        if previous_error:
            logger.info(f"Attempting to correct previous error: {previous_error}")
        
        if not retrieved_schema_examples:
            # 스키마가 없는 경우 기본 스키마 사용
            logger.warning("No schema examples available, using default schema")
            retrieved_schema_examples = get_basic_schema_examples()
            
            if not retrieved_schema_examples:
                return {
                    "messages": [AIMessage(content="Cannot generate SQL: No table schema available.")],
                    "final_query": "",
                    "error_message": "Missing table schema"
                }
        
        # SQL 생성 프롬프트 구성
        system_prompt = self._build_sql_generation_prompt()
        
        evidences = f"회사명or종목명-exchange_kosdaq_stock_master.kor_name_small"
        evidences += str(retrieved_sample_query)
        
        # 이전 에러가 있으면 프롬프트에 포함
        if previous_error:
            error_context = f"\n\nPrevious SQL execution failed with error:\n{previous_error}\n\nPlease analyze the error and correct the SQL query accordingly."
            prompt = system_prompt.format(
                db_details=retrieved_schema_examples,
                evidence=evidences,
                question=user_query + error_context
            )
        else:
            prompt = system_prompt.format(
                db_details=retrieved_schema_examples,
                evidence=evidences,
                question=user_query
            )
        
        # 캐시에서 SQL 조회 시도 (샘플 쿼리 포함)
        schema_info = str(retrieved_schema_examples) + ":::" + str(retrieved_sample_query)
        cached_sql = llm_cache_manager.get_cached_sql(user_query, schema_info)
        
        if cached_sql:
            logger.info(f"Using cached SQL query (with sample): {cached_sql}")
            retry_count = state.get("retry_count", 0)
            return {
                **state,
                "messages": [AIMessage(content=f"Generated SQL query (from cache):\n```sql\n{cached_sql}\n```")],
                "final_query": cached_sql,
                "error_message": None,
                "retry_count": retry_count + 1
            }
        
        try:
            retry_count = state.get("retry_count", 0)
            response = self._llm.invoke(prompt)
            logger.info(f"LLM response: {response}")
            
            # SQL 쿼리 추출
            sql_query = self._extract_sql_from_response(response)
            logger.info(f"Generated SQL (Attempt): {sql_query}")
            
            # 성공적으로 생성된 SQL 캐싱
            if sql_query:
                llm_cache_manager.set_cached_sql(user_query, schema_info, sql_query)
            
            return {
                **state,
                "messages": [AIMessage(content=f"Generated SQL query attempt:\n```sql\n{sql_query}\n```")],
                "final_query": sql_query,
                "error_message": None,
                "retry_count": retry_count + 1
            }
            
        except Exception as e:
            logger.error(f"Error invoking LLM for SQL generation: {e}")
            err_msg = f"LLM failed during query generation: {e}"
            return {
                **state,
                "messages": [AIMessage(content=f"Error generating SQL: {err_msg}")],
                "final_query": "",
                "error_message": err_msg,
                "retry_count": state.get("retry_count", 0) + 1
            }
    
    def _build_sql_generation_prompt(self) -> str:
        """SQL 생성 프롬프트 구성"""
        return '''Task Overview:
You are a data science expert. Below, you are provided with a database schema and a natural language question. Your task is to understand the schema and generate a valid SQL query to answer the question.

Database Engine:
PostgreSQL

Database Schema:
{db_details}
This schema describes the database's structure, including tables, columns, primary keys, foreign keys, and any relevant relationships or constraints.

Reference information:
{evidence}

Question:
{question}

Instructions:
- Accurately reflects the user's specific request.
- Strictly use the given Database Schema and do not create new column or table name.
- Is complete, ending with a semicolon, and avoids truncation.
- Produces consistent output for repeated or similar requests.
- Do not include any explanations, markdown, or incomplete queries.
- If a previous SQL execution error is mentioned, carefully analyze the error message and correct the column names, table names, or syntax accordingly.
- Pay special attention to hints in error messages (e.g., "Perhaps you meant to reference the column...").

Output Format:
In your answer, please enclose the generated SQL query in a code block:
```sql
-- Your SQL query
```
'''
    
    def _extract_sql_from_response(self, response: str) -> str:
        """LLM 응답에서 SQL 쿼리 추출"""
        # OpenAI 인터페이스의 경우 response가 객체일 수 있음
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        # 다양한 패턴으로 SQL 추출 시도
        patterns = [
            r"```sql\n(.*?)\n```",  # 기본 패턴
            r"```sql\n(.*?)```",    # 줄바꿈 없는 패턴
            r"`sql\n(.*?)`",        # 백틱 하나 패턴
            r"```\n(.*?)\n```",     # sql 키워드 없는 패턴
            r"```(.*?)```",         # 단순 패턴
            r"`sql(.*?)`"           # 백틱 하나로 sql 키워드 포함
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                sql_query = match.group(1).strip()
                # 'sql' 키워드가 쿼리 앞에 붙어있으면 제거
                if sql_query.lower().startswith('sql'):
                    sql_query = sql_query[3:].strip()
                return sql_query
        
        # 패턴 매칭 실패 시 전체 텍스트에서 추출
        sql_query = response_text.strip()
        
        # 다양한 접두사 처리
        if sql_query.startswith("::sql"):
            sql_query = sql_query[5:].strip()  # ::sql 제거
        elif sql_query.startswith("`sql"):
            sql_query = sql_query[4:]  # `sql 제거
            if sql_query.endswith("`"):
                sql_query = sql_query[:-1]
        elif sql_query.startswith("`"):
            sql_query = sql_query[1:]
            if sql_query.endswith("`"):
                sql_query = sql_query[:-1]
        elif sql_query.lower().startswith('sql'):
            sql_query = sql_query[3:].strip()
        
        # 마크다운 코드 블록 제거
        if sql_query.startswith("```sql"):
            sql_query = sql_query[len("```sql"):]
        elif sql_query.startswith("```"):
            sql_query = sql_query[len("```"):]
        
        if sql_query.endswith("```"):
            sql_query = sql_query[:-len("```")]
        
        sql_query = sql_query.strip()
        
        # 'sql' 키워드가 쿼리 앞에 붙어있으면 제거
        if sql_query.lower().startswith('sql'):
            sql_query = sql_query[3:].strip()
        
        return sql_query
    
    def _check_sql_query(self, state: TextToSqlState) -> dict:
        """SQL 쿼리 구문 검사"""
        final_query = state.get("final_query", "")
        error_msg = None
        message_content = "SQL query syntax check: "
        
        if not final_query:
            error_msg = "No SQL query was generated to check."
            logger.error(error_msg)
            message_content += "FAILED (No query provided)."
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=message_content)],
                "error_message": error_msg
            }
        
        try:
            checker_result = self._sql_tools['query_checker'].invoke({"query": final_query})
            logger.info(f"Query check raw result: {checker_result}")
            
            if isinstance(checker_result, str) and "error" in checker_result.lower():
                raise ValueError(f"Syntax error reported by checker: {checker_result}")
            
            message_content += "Passed."
            logger.info("Syntax check passed.")
            
        except Exception as e:
            error_msg = f"Syntax check failed: {e}"
            logger.error(error_msg)
            message_content += f"FAILED\nError: {error_msg}"
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=message_content)],
            "error_message": error_msg
        }
    
    def _execute_sql_query(self, state: TextToSqlState) -> dict:
        """SQL 쿼리 실행"""
        final_query = state.get("final_query", "")
        logger.info(f"Executing SQL query: {final_query}")
        
        query_result_val = None
        error_msg = None
        message_content = "SQL query execution: "
        
        if not final_query:
            error_msg = "Cannot execute: No SQL query available."
            logger.error(error_msg)
            message_content += "SKIPPED (No query)."
            return {
                **state,
                "messages": [AIMessage(content=message_content)],
                "error_message": error_msg,
                "query_result": "Execution Skipped"
            }
        
        try:
            query_result_val = db_manager.execute_sync_query(final_query)
            logger.info(f"Query execution successful. Result preview: {str(query_result_val)[:200]}...")
            message_content += f"Successful.\nResult:\n{str(query_result_val)}"
            
        except Exception as e:
            error_msg = f"Execution failed: {e}"
            logger.error(error_msg)
            message_content += f"FAILED\nError: {error_msg}"
        
        return {
            **state,
            "messages": [AIMessage(content=message_content)],
            "query_result": str(query_result_val) if error_msg is None else f"Execution Error: {error_msg}",
            "error_message": error_msg
        }
    
    def _decide_after_check(self, state: TextToSqlState) -> Literal["execute_sql_query", "get_sample_query_from_vector_db"]:
        """구문 검사 후 다음 단계 결정 (무한 루프 방지)"""
        current_retry_count = state.get("retry_count", 0)
        max_retries = config.max_text_to_sql_retries
        
        if state.get("error_message") and current_retry_count < max_retries:
            logger.info(f"Decision: Syntax check failed (attempt {current_retry_count + 1}/{max_retries}), routing back to get_sample_query_from_vector_db.")
            return "get_sample_query_from_vector_db"
        else:
            if current_retry_count >= max_retries:
                logger.warning(f"Max retries reached ({max_retries}), proceeding to execute despite errors")
            else:
                logger.info("Decision: Syntax check passed, routing to execute_sql_query.")
            return "execute_sql_query"
    
    def _decide_after_execute(self, state: TextToSqlState) -> Literal["generate_answer", "get_sample_query_from_vector_db", END]:
        """실행 후 다음 단계 결정 (무한 루프 방지)"""
        current_retry_count = state.get("retry_count", 0)
        max_retries = config.max_text_to_sql_retries
        
        if state.get("error_message"):
            if current_retry_count >= max_retries:
                logger.warning(f"Max retries reached ({max_retries}) for Text-to-SQL. Ending this sub-graph.")
                # 최대 재시도 횟수에 도달했을 때도 답변 생성 시도
                return "generate_answer"
            else:
                logger.info(f"Decision: Execution failed (attempt {current_retry_count + 1}/{max_retries}). Routing back to get_sample_query_from_vector_db.")
                return "get_sample_query_from_vector_db"
        else:
            logger.info("Decision: Execution successful, routing to generate_answer.")
            return "generate_answer"
    
    def _generate_answer(self, state: TextToSqlState) -> dict:
        """SQL 실행 결과를 자연어 답변으로 변환 (실패 시에도 최선의 답변 제공)"""
        query_result = state.get("query_result", "")
        final_query = state.get("final_query", "")
        messages = state.get("messages", [])
        error_message = state.get("error_message")
        
        # 원본 사용자 쿼리 가져오기
        user_query = messages[0].content if messages and hasattr(messages[0], 'content') else ""
        
        logger.info("Generating natural language answer from SQL results")
        
        # 에러가 있는 경우 처리
        if error_message and "Execution Error" in str(query_result):
            prompt = f"""사용자의 질문에 대한 SQL 쿼리 실행이 실패했습니다. 오류 내용을 설명하고 가능한 대안을 제시해주세요.

사용자 질문: {user_query}

시도한 SQL 쿼리:
{final_query}

오류 메시지:
{error_message}

답변 작성 가이드라인:
1. 오류가 발생한 이유를 간단히 설명해주세요
2. 가능한 경우 대안이나 해결 방법을 제시해주세요
3. 사용자가 이해하기 쉬운 언어로 설명해주세요

답변:"""
        else:
            # 정상 실행된 경우
            prompt = f"""사용자의 질문에 대한 SQL 쿼리 실행 결과를 바탕으로 자연스러운 한국어 답변을 생성해주세요.

사용자 질문: {user_query}

실행된 SQL 쿼리:
{final_query}

쿼리 실행 결과:
{query_result}

답변 작성 가이드라인:
1. 쿼리 결과를 사용자가 이해하기 쉽게 설명해주세요
2. 숫자는 한국어 표기법에 맞게 표시하세요 (예: 1000000000 → 10억)
3. 결과가 없는 경우 "조건에 맞는 데이터가 없습니다"라고 안내하세요
4. 테이블 형태로 보여줄 때는 마크다운 표를 사용하세요
5. 종목코드와 함께 종목명도 함께 표시해주세요 (가능한 경우)

답변:"""
        
        try:
            # LLM을 사용하여 답변 생성
            response = self._llm.invoke(prompt)
            # OpenAI 인터페이스의 경우 response가 문자열일 수 있음
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            logger.info("Natural language answer generated successfully")
            
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=f"Final Answer: {answer}")],
                "final_answer": answer
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            
            # 실패 시 상황에 맞는 기본 답변
            if error_message:
                fallback_answer = f"죄송합니다. SQL 쿼리 실행 중 오류가 발생했습니다.\n\n"
                fallback_answer += f"오류 내용: {error_message}\n\n"
                fallback_answer += "다른 조건으로 다시 시도해 주시기 바랍니다."
            else:
                fallback_answer = f"쿼리 실행 결과: {query_result}"
            
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=f"Final Answer: {fallback_answer}")],
                "final_answer": fallback_answer
            }
    
    def _build_graph(self):
        """LangGraph 구성"""
        graph_builder = StateGraph(TextToSqlState)
        
        # 노드 추가
        graph_builder.add_node("get_schema_from_vector_db", self._get_schema_from_vector_db)
        graph_builder.add_node("get_sample_query_from_vector_db", self._get_sample_query_from_vector_db)
        graph_builder.add_node("generate_sql_query_with_schema", self._generate_sql_query_with_schema)
        graph_builder.add_node("generate_sql_query_with_sample", self._generate_sql_query_with_sample)
        graph_builder.add_node("check_sql_query", self._check_sql_query)
        graph_builder.add_node("execute_sql_query", self._execute_sql_query)
        graph_builder.add_node("generate_answer", self._generate_answer)
        
        # 엣지 구성
        graph_builder.set_entry_point("get_schema_from_vector_db")
        graph_builder.add_edge("get_schema_from_vector_db", "generate_sql_query_with_schema")
        graph_builder.add_edge("generate_sql_query_with_schema", "check_sql_query")
        graph_builder.add_edge("generate_sql_query_with_sample", "check_sql_query")
        graph_builder.add_edge("get_sample_query_from_vector_db", "generate_sql_query_with_sample")
        graph_builder.add_edge("generate_answer", END)  # answer 노드는 항상 END로
        graph_builder.add_conditional_edges("check_sql_query", self._decide_after_check)
        graph_builder.add_conditional_edges("execute_sql_query", self._decide_after_execute)
        
        # 그래프 컴파일
        self._graph = graph_builder.compile()
        logger.info("Text-to-SQL graph compiled successfully")
    
    @observe() if LANGFUSE_AVAILABLE else lambda x: x
    def query(self, user_query: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> dict:
        """사용자 쿼리를 SQL로 변환하고 실행"""
        try:
            # Langfuse 추적 설정
            if session_id or user_id:
                langfuse_manager.update_session(session_id, user_id)
            
            # 현재 trace에 session과 user 정보 업데이트
            current_session_id = session_id or langfuse_manager.session_id
            current_user_id = user_id or langfuse_manager.user_id
            
            # Langfuse trace 업데이트 (대시보드 표시용)
            if LANGFUSE_AVAILABLE and current_session_id and current_user_id:
                try:
                    langfuse_client = get_client()
                    langfuse_client.update_current_trace(
                        session_id=current_session_id,
                        user_id=current_user_id,
                        tags=["text-to-sql", "m-asset-api"],
                        metadata={
                            "agent_type": "text_to_sql",
                            "query": user_query
                        }
                    )
                    logger.info(f"Langfuse trace updated with session: {current_session_id}, user: {current_user_id}")
                except Exception as e:
                    logger.warning(f"Failed to update Langfuse trace: {e}")
            
            # 입력 구성
            inputs = {"messages": [HumanMessage(content=user_query)]}
            
            # 그래프 실행 (콜백 핸들러와 함께)
            callback_handler = langfuse_manager.get_callback_handler()
            if callback_handler:
                # 세션 정보가 있는 새로운 CallbackHandler 생성
                try:
                    if CallbackHandler:
                        session_callback = CallbackHandler(
                            session_id=current_session_id,
                            user_id=current_user_id
                        )
                    else:
                        session_callback = callback_handler
                    config_data = {
                        "callbacks": [session_callback],
                        "metadata": {
                            "session_id": current_session_id,
                            "user_id": current_user_id,
                            "agent_type": "text_to_sql",
                            "query": user_query
                        },
                        "tags": [f"session:{current_session_id}", f"user:{current_user_id}"],
                        "recursion_limit": 150  # 재귀 한계를 150으로 증가 (동시성 환경 고려)
                    }
                except TypeError:
                    # session_id, user_id가 지원되지 않는 경우 기본 방식 사용
                    config_data = {
                        "callbacks": [callback_handler],
                        "metadata": {
                            "session_id": current_session_id,
                            "user_id": current_user_id,
                            "agent_type": "text_to_sql",
                            "query": user_query
                        },
                        "tags": [f"session:{current_session_id}", f"user:{current_user_id}"],
                        "recursion_limit": 150  # 재귀 한계를 150으로 증가 (동시성 환경 고려)
                    }
                result = self._graph.invoke(inputs, config=config_data)
            else:
                # Langfuse 없을 때도 recursion_limit 적용
                config_data = {"recursion_limit": 150}
                result = self._graph.invoke(inputs, config=config_data)
            
            logger.info("Text-to-SQL query processing completed")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            traceback.print_exc()
            raise
    
    def get_graph(self):
        """그래프 인스턴스 반환 (테스트용)"""
        return self._graph


# 전역 Text-to-SQL 에이전트 인스턴스
text_to_sql_agent = TextToSqlAgent()