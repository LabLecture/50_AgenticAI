"""
Main entry point for the M-Asset POC application.
Provides CLI interface and server startup options.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.agents.text_to_sql_agent import text_to_sql_agent
from src.utils.weaviate_setup import weaviate_setup
from src.core.langfuse_manager import langfuse_manager

# 로깅 설정
from src.utils.logging_config import setup_logging, get_log_config_from_env, get_logger

# 환경 변수에서 로그 설정 읽기
log_config = get_log_config_from_env()
setup_logging(**log_config)
logger = get_logger(__name__)


def run_server():
    """API 서버 실행"""
    import uvicorn
    from src.api.server import app
    
    logger.info(f"Starting M-Asset POC API Server on {config.api.host}:{config.api.port}")
    
    # Uvicorn 로그 설정
    from src.utils.logging_config import setup_uvicorn_logging
    uvicorn_log_config = setup_uvicorn_logging(log_config.get("log_level", "INFO"))
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        log_config=uvicorn_log_config
    )


def setup_weaviate():
    """Weaviate 벡터 스토어 초기 설정 (기존 데이터가 없을 때만)"""
    logger.info("Setting up Weaviate vector store...")
    
    try:
        weaviate_setup.initialize()
        
        # 기존 컬렉션 확인
        if weaviate_setup.check_existing_collections():
            logger.info("Existing Weaviate collections found. Skipping data initialization.")
            logger.info("Using existing schema and sample collections.")
            weaviate_setup.close()
            return True
        
        # 기존 컬렉션이 없을 때만 새로 생성
        logger.info("No existing collections found. Creating new collections...")
        success = weaviate_setup.setup_complete_schema_collection()
        
        if success:
            logger.info("Weaviate setup completed successfully")
        else:
            logger.error("Weaviate setup failed")
            return False
            
        weaviate_setup.close()
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Weaviate: {e}")
        return False


def test_query(query: str, session_id: str = None, user_id: str = None):
    """테스트 쿼리 실행"""
    logger.info(f"Testing query: {query}")
    
    try:
        # 에이전트로 쿼리 실행
        result = text_to_sql_agent.query(query, session_id, user_id)
        
        print("\n=== Query Result ===")
        print(f"Original Query: {query}")
        print(f"Generated SQL: {result.get('final_query', 'N/A')}")
        print(f"Execution Result: {result.get('query_result', 'N/A')}")
        
        if result.get('error_message'):
            print(f"Error: {result.get('error_message')}")
        
        # Langfuse 플러시
        langfuse_manager.flush()
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing query: {e}")
        return None


def interactive_mode():
    """대화형 모드"""
    print("=== M-Asset POC Interactive Mode ===")
    print("Enter your queries (type 'exit' to quit):")
    
    session_id = "interactive_session"
    user_id = "interactive_user"
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                continue
            
            result = test_query(query, session_id, user_id)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="M-Asset POC Application")
    parser.add_argument("--mode", choices=["server", "setup", "test", "interactive", "check", "excel", "a2a"], 
                       default="server", help="실행 모드")
    parser.add_argument("--query", type=str, help="테스트 쿼리 (test 모드용)")
    parser.add_argument("--session-id", type=str, help="세션 ID")
    parser.add_argument("--user-id", type=str, help="사용자 ID")
    parser.add_argument("--input", type=str, help="입력 Excel 파일 경로 (excel 모드용)")
    parser.add_argument("--output", type=str, help="출력 Excel 파일 경로 (excel 모드용)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "server":
            run_server()
            
        elif args.mode == "setup":
            success = setup_weaviate()
            sys.exit(0 if success else 1)
            
        elif args.mode == "test":
            if not args.query:
                print("Error: --query argument is required for test mode")
                sys.exit(1)
            
            result = test_query(args.query, args.session_id, args.user_id)
            sys.exit(0 if result else 1)
            
        elif args.mode == "interactive":
            interactive_mode()
            
        elif args.mode == "check":
            # Weaviate 연결 및 컬렉션 확인
            try:
                weaviate_setup.initialize()
                if weaviate_setup.check_existing_collections():
                    print("✅ 기존 Weaviate 컬렉션이 발견되었습니다.")
                    print("바로 서버를 실행할 수 있습니다: python main.py --mode server")
                else:
                    print("❌ 기존 Weaviate 컬렉션이 없습니다.")
                    print("초기 설정을 실행하세요: python main.py --mode setup")
                weaviate_setup.close()
            except Exception as e:
                print(f"❌ Weaviate 연결 실패: {e}")
                print("Weaviate 서버가 실행 중인지 확인하거나 WEAVIATE_ENABLED=false로 설정하세요.")
                
        elif args.mode == "excel":
            # Excel 배치 처리
            if not args.input:
                print("Error: --input argument is required for excel mode")
                sys.exit(1)
            
            from pathlib import Path
            from query_withexcel import process_excel_batch
            
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ 입력 파일을 찾을 수 없습니다: {input_path}")
                sys.exit(1)
            
            if not input_path.suffix.lower() in ['.xlsx', '.xls']:
                print(f"❌ Excel 파일이 아닙니다: {input_path}")
                sys.exit(1)
            
            print(f"📁 입력 파일: {input_path}")
            if args.output:
                print(f"📁 출력 파일: {args.output}")
            print("-" * 50)
            
            try:
                # Excel 배치 처리 실행
                process_excel_batch(
                    excel_file_path=str(input_path),
                    text_to_sql_app=text_to_sql_agent,
                    output_file_path=args.output
                )
                print("✅ Excel 배치 처리가 완료되었습니다.")
                
            except Exception as e:
                print(f"❌ Excel 배치 처리 오류: {e}")
                sys.exit(1)
                
        elif args.mode == "a2a":
            # A2A 독립형 서버 실행
            print("🤖 A2A (Agent-to-Agent) 모드로 서버를 시작합니다...")
            
            if not config.a2a.enabled:
                print("❌ A2A가 비활성화되어 있습니다.")
                print("환경 변수에서 A2A_ENABLED=true로 설정하세요.")
                sys.exit(1)
            
            try:
                # A2A 독립형 서버 import 및 실행
                import asyncio
                from src.a2a.standalone_server import A2AStandaloneServer
                
                async def run_a2a_server():
                    server = A2AStandaloneServer()
                    await server.start()
                
                print(f"🚀 A2A 서버가 {config.a2a.base_url}에서 시작됩니다...")
                asyncio.run(run_a2a_server())
                
            except ImportError as e:
                print(f"❌ A2A SDK가 설치되지 않았습니다: {e}")
                print("A2A SDK를 설치하세요: pip install a2a-sdk")
                sys.exit(1)
            except Exception as e:
                print(f"❌ A2A 서버 시작 오류: {e}")
                sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()