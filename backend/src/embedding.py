import os
import shutil

from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core import ServiceContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import LangchainNodeParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

from llama_index.core import Settings

import chromadb
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # 디렉토리 설정
    file_path = Path("../data")
    directory = Path("../vector_store")
    
    # 기존 벡터 스토어 삭제
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"기존 벡터 스토어 삭제됨: {directory}")

    # HuggingFace 임베딩 모델 초기화
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # ChromaDB 클라이언트 생성
    chroma_client = chromadb.PersistentClient(path=str(directory))

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

    # LangchainNodeParser 생성
    node_parser = LangchainNodeParser(text_splitter)

    Settings.embed_model = embed_model
    Settings.node_parser = node_parser    

    # PDF 파일 처리
    for pdf_file in file_path.glob("*.pdf"):
        print(f"Processing {pdf_file}...")
        
        # PDF 파일 로드
        documents = SimpleDirectoryReader(input_files=[str(pdf_file)]).load_data()

        # VectorStoreIndex 생성 및 문서 추가
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
        )

    # 변경사항 저장
    index.storage_context.persist()

    print("Embedding process completed.")