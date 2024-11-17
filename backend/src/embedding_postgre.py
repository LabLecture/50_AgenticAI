import os
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext

from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

from llama_index.core.schema import TextNode, Document      # postgre vector store
from llama_index.core.node_parser import SentenceSplitter
from llama_parse import LlamaParse
from llama_index.vector_stores.postgres import PGVectorStore

import pandas as pd
import numpy as np

from pathlib import Path
from datetime import datetime

# Load environment variables
load_dotenv(verbose=True)

class ExcelReader:
    """엑셀 파일을 읽어서 Document 객체로 변환하는 클래스"""
    def __init__(self):
        pass

    def load_data(self, file, extra_info=None):
        df = pd.read_excel(file)
        docs = []
        for _, row in df.iterrows():
            metadata = {
                'keyword': self.handle_nan(row['keyword']),
                'page': self.handle_nan(row['page']),
                'plaintiff': self.handle_nan(row['plaintiff']),
                'defendant': self.handle_nan(row['defendant']),
                'another': self.handle_nan(row['another']),
                'money': self.handle_nan(row['money']),
                'unit': self.handle_nan(row['unit']),
                'etc': self.handle_nan(row['etc']),
                'interest_rate': self.handle_nan(row['interest rate']),
                'time_start': self.format_date(row['time_start']),
                'time_end': self.format_date(row['time_end']),
                'time_start_txt': self.handle_nan(row['time_start']),
                'time_end_txt': self.handle_nan(row['time_end'])
            }
            if extra_info:
                metadata.update(extra_info)
            # 문서 내용 생성 및 Document 객체로 변환
            content = f"{self.handle_nan(row['plaintiff'])} {self.handle_nan(row['defendant'])} {self.handle_nan(row['another'])} {self.handle_nan(row['money'])} {self.handle_nan(row['unit'])} {self.handle_nan(row['etc'])} {self.handle_nan(row['text'])}"
            doc = Document(text=content.strip(), metadata=metadata)
            docs.append(doc)
        return docs
    
    def handle_nan(self, value):
        if pd.isna(value) or value is None:
            return ''
        elif isinstance(value, float) and np.isnan(value):
            return ''
        return str(value)

    def format_date(self, date_value):
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        elif pd.isna(date_value):
            return ''
        else:
            return str(date_value)

def load_files(input_dir):

    # 디렉토리 내의 모든 파일 경로를 리스트로 수집
    file_paths = []
    for ext in [".pdf", ".xlsx", ".xls"]:  # 처리하고자 하는 파일 확장자
        file_paths.extend(list(input_dir.glob(f"*{ext}")))  # glob 잡아냄.
    
    if not file_paths:
        raise ValueError(f"No supported files found in {input_dir}")
        
    print(f"Found files: {[f.name for f in file_paths]}")
    
    parser = LlamaParse(
        api_key="llx-JItT6ZbUs6c05fS0nNr3luAD13gxvfPouCrnwmNbZlv2nblg", # llama_index
        result_type="markdown",                     # "markdown" and "text" are available
        verbose=True,
    )
        
    excel_reader = ExcelReader()
    file_extractor = {              
        ".pdf": parser,
        ".xlsx": excel_reader,
        ".xls": excel_reader
    }
    reader = SimpleDirectoryReader(                 # 다양한 형식 문서 읽기
        input_files=[str(p) for p in file_paths],   # Path 객체를 문자열로 변환
        file_extractor=file_extractor
    )
    docs = reader.load_data()
    
    return docs  

def split(docs):
    """문서를 일정 크기의 청크로 분할"""
    indexing = SentenceSplitter(chunk_size=512, chunk_overlap=0)        
    nodes = indexing.get_nodes_from_documents(docs)                 # Document 객체들을 TextNode 객체로 변환하며 분할
    return nodes

def is_doc(obj):
    if isinstance(obj, Document):       # vector_index  pdf 파일 대상.
        return True
    elif isinstance(obj, TextNode):     # vector_index  일반 text 대상
        return False
    return None

def create_index(docs, schema_name="public", table_name="tmp"):
    """PostgreSQL 벡터 저장소 생성 및 문서 인덱싱"""
    vector_store = PGVectorStore.from_params(   # PostgreSQL 벡터 저장소 설정
        database    = "skku",
        host        = "192.168.1.204",
        password    = "aithepwd8#",
        port        = "55432",
        user        = "aitheuser1",
        schema_name = schema_name,
        table_name  = table_name,
        embed_dim   = 384,
    )
    
    # StorageContext는 벡터 저장소의 설정과 상태를 관리 : 벡터 저장소 초기화, 인덱스 설정, 메타데이터 관리, 저장소 연결 관리
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # embed_model = OpenAIEmbedding()
    
    doc_or_node = is_doc(docs[0])

    if doc_or_node is None:
        raise ValueError()

    # 문서 유형에 따른 인덱스 생성
    try:
        if doc_or_node:
            index = VectorStoreIndex.from_documents(docs,   # vector_index  pdf 파일 대상.
                                                    storage_context=storage_context,
                                                    show_progress=True, 
                                                    embed_model=embed_model)
        else:
            index = VectorStoreIndex(docs,                  # vector_index  일반 text 대상
                                    storage_context=storage_context,
                                    show_progress=True, 
                                    embed_model=embed_model)
        return index
    except Exception as e:
        print("create_index Exception:", str(e))
        return None
if __name__ == "__main__":
    try:
        file_path = Path("../data").resolve()
        docs = load_files(file_path)            # file을 parsing 한 docs로 변환
        nodes = split(docs)                     # parsing 한 docs를 split
        index = create_index(nodes, schema_name="public", table_name="tmp_chatbot") 
        # Vector store 에 저장(indexing)
        
        if index is not None:
            index.storage_context.persist()             # 벡터 스토어에 메모리에 유지
            print("Embedding Postgre Success")
            
    except Exception as e:
        print("Embedding Postgre create_vector_store Exception:", str(e))

     