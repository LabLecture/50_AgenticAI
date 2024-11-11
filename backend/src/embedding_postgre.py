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

# import chromadb
from dotenv import load_dotenv

from llama_index.core.schema import TextNode, Document      # postgre vector store
from llama_index.core.node_parser import SentenceSplitter
from llama_parse import LlamaParse
from llama_index.vector_stores.postgres import PGVectorStore

import pandas as pd
import numpy as np


load_dotenv()

class ExcelReader:
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

def load_files(input_files):
    
    parser = LlamaParse(
        api_key="llx-JItT6ZbUs6c05fS0nNr3luAD13gxvfPouCrnwmNbZlv2nblg",
        result_type="markdown",  # "markdown" and "text" are available
        verbose=True,
    )
        
    excel_reader = ExcelReader()
    file_extractor = {
        ".pdf": parser,
        ".xlsx": excel_reader,
        ".xls": excel_reader
    }
    reader = SimpleDirectoryReader(
        input_files=input_files
    )
    docs = reader.load_data()
    
    return docs  

def split(docs):
    
    indexing = SentenceSplitter(chunk_size=512, chunk_overlap=0)        
    nodes = indexing.get_nodes_from_documents(docs)
    return nodes

def is_doc(obj):
    if isinstance(obj, Document):       # vector_index  pdf 파일 대상.
        return True
    elif isinstance(obj, TextNode):     # vector_index  일반 text 대상
        return False
    return None

def create_index(docs, schema_name="public", table_name="tmp"):
    vector_store = PGVectorStore.from_params(
        database    = "skku",
        host        = "192.168.1.239",
        password    = "aithepwd8#",
        port        = "55432",
        user        = "aitheuser1",
        schema_name = schema_name,
        table_name  = table_name,
        embed_dim   = 1536,
    )
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    doc_or_node = is_doc(docs[0])

    if doc_or_node is None:
        raise ValueError()

    # 디버깅 결과 밑의 VectorStoreIndex 부분이 실행되서 Index가 리턴될 때 테이블이 추가됨..
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
        return None

def insert_vector_store(db: Session, vector_store_create: VectorStoreCreate):
    # print("crud insert_vector_store --> vector_store_create ", vector_store_create)
    
    vector_store = VectorStore(
        dataset_sq=vector_store_create.dataset_sq,
        eval_dataset_sq=None,
        strategy_id=vector_store_create.indexing_strategy,
        vector_store_name=vector_store_create.vector_store_name,
        vector_store_schema=vector_store_create.schema_name,
        vector_store_table=vector_store_create.table_name,
        vector_store_desc=vector_store_create.etc,
        display_order=vector_store_create.order,
        hybrid_yn=vector_store_create.hybrid_yn
    )
    try:
        # print("crud insert_vector_store --> vector_store ", vector_store)
        
        result = db.add(vector_store)
        # print("crud insert_vector_store --> result ", result)
        
        db.commit()
        # return result
        return {"message": "Success"}
    except Exception as e:
        db.rollback()
        print("crud insert_vector_store Exception :", str(e))
        return {"error": str(e)}

if __name__ == "__main__":
    # 디렉토리 설정
    file_path = Path("../data")
    try:
        connection_string = os.environ["POSTGRESQL_CONNECTION_STRING"]
        file_path = Path("../data")

        docs = load_files(file_path)
        nodes = split(docs)
        index = create_index(nodes, schema_name="public", table_name="tmp_chatbot")
        
        if index != None:
            response = insert_vector_store(db, vector_store)
        if (response == "Success"):
            print("Embedding Postgre Success")
        else:
            print("Embedding Postgre Failed ")
    except Exception as e:
        print("Embedding Postgre create_vector_store Exception :", str(e))        