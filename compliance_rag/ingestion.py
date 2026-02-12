import os
import shutil
from typing import List
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from compliance_rag.config import llm_config, DATA_DIR, VECTOR_STORE_PATH

def ingest_compliance_docs():
    """
    Ingests compliance documents from the data directory into a FAISS vector store.
    This mirrors the 'Preparing the Knowledge Stores' step in the tutorial.
    """
    print(f"--- Starting Data Ingestion from {DATA_DIR} ---")
    
    # 1. Load Documents
    # We support PDFs and Text files for now
    loaders = [
        DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
        DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader),
        DirectoryLoader(DATA_DIR, glob="**/*.md", loader_cls=TextLoader)
    ]
    
    raw_docs: List[Document] = []
    for loader in loaders:
        try:
            raw_docs.extend(loader.load())
        except Exception as e:
            print(f"Warning: Could not load some documents: {e}")
            
    print(f"Loaded {len(raw_docs)} raw documents.")
    
    if not raw_docs:
        print("No documents found to ingest. Skipping vector store creation.")
        return

    # 2. Split Text
    # Splitting is crucial for RAG. We use overlap to maintain context across chunks.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    
    splits = text_splitter.split_documents(raw_docs)
    print(f"Split into {len(splits)} chunks.")

    # 3. Create Vector Store
    # We use FAISS (Facebook AI Similarity Search) with our local embeddings
    print("Creating FAISS vector store... this may take a moment.")
    vectorstore = FAISS.from_documents(
        documents=splits,
        embedding=llm_config["embedding_model"]
    )
    
    # 4. Save Index
    # Persist to disk so we don't have to rebuild every time
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)
    
    vectorstore.save_local(VECTOR_STORE_PATH)
    print(f"Vector store saved to {VECTOR_STORE_PATH}")

if __name__ == "__main__":
    ingest_compliance_docs()
