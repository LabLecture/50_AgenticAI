import os
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import RecursiveCharacterTextSplitter

from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.embeddings import HuggingFaceEmbedding
import chromadb
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # 디렉토리 설정
    data_dir = Path("../data")
    vector_store_dir = Path("../vector_store")

    # 벡터 스토어 디렉토리가 없으면 생성
    vector_store_dir.mkdir(parents=True, exist_ok=True)

    # HuggingFace 임베딩 모델 초기화
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # ChromaDB 클라이언트 생성
    chroma_client = chromadb.PersistentClient(path=str(vector_store_dir))

    # ChromaDB 컬렉션 생성 또는 불러오기
    chroma_collection = chroma_client.get_or_create_collection("my_collection")

    # ChromaVectorStore 생성
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # StorageContext 생성
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
    )

    # ServiceContext 생성
    service_context = ServiceContext.from_defaults(
        embed_model=embed_model,
        text_splitter=text_splitter
    )

    # PDF 파일 처리
    for pdf_file in data_dir.glob("*.pdf"):
        print(f"Processing {pdf_file}...")
        
        # PDF 파일 로드
        documents = SimpleDirectoryReader(input_files=[str(pdf_file)]).load_data()

        # VectorStoreIndex 생성 및 문서 추가
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            service_context=service_context,
        )

    # 변경사항 저장
    index.storage_context.persist()

    print("Embedding process completed.")