import os
import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    directory = '../vector_store'
    file_path = Path("../data")
    
    # 기존 벡터 스토어 삭제
    # if os.path.exists(directory):
    #     shutil.rmtree(directory)
    #     print(f"기존 벡터 스토어 삭제됨: {directory}")
    
    # embeddings_model = OpenAIEmbeddings()
    # HuggingFaceEmbeddings 초기화
    # 임베딩 모델 설정
    embedding_model_id = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings_model = HuggingFaceEmbeddings(
        model_name=embedding_model_id,
        model_kwargs={'device': 'cpu'}
    )      

    for file in file_path.glob("*.pdf"):
        loader = PyPDFLoader(str(file))
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False
        )

        docs = loader.load_and_split(text_splitter)

        
        vector_store = Chroma.from_documents(
            docs,
            embeddings_model,
            persist_directory=directory
        )
    print(f"벡터 스토어 생성완료 : {directory}")


    # docs = vector_store.similarity_search("소비자 물가 전망 알려줘")

    # for idx, doc in enumerate(docs, 1):
    #     print(f"Document {idx}")
    #     print(doc.page_content)
    #     print()
